from odoo import api, fields, models,_
from odoo.exceptions import UserError
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'
    customer_ref = fields.Char('Customer Ref')



class SaleOrderInharit(models.Model):

    _inherit = 'sale.order'

    def copy_new(self, default=None):
       new_sale = self.id
       self.is_new_order = True
       print(new_sale,'id')
       new_sale = self.copy()
       return {
           'type' : 'ir.actions.act_window',
           'res_model' : 'sale.order',
           'res_id' : new_sale.id,
           'is_new_order' : False,
           'views' : [[False, 'form']],
       }



    vendor_id = fields.Many2one('res.partner', string='Vendor', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    invoice_amount = fields.Float('Invoice Pay Amount',store=True,copy=False)
    pay_percentage = fields.Integer('Pay Percentage',readonly=False,copy=False)
    project_id = fields.Many2one('project.project',string='Project Name')
    account_id = fields.One2many('account.move', 'account_custom_id','فواتير العملاء')
    date_order_custom = fields.Date(string="Order Date Create",default=fields.Date.today ,store=True,readonly=True)
    rec_line = fields.One2many("receipt.report", "sale_id", copy=False)
    customer_ref = fields.Char('Customer Ref',related='partner_id.customer_ref')
    attn_ref = fields.Char('Attn')

    dear = fields.Text('Dear :')
    terms = fields.Text('Terms :')
    terms_payment = fields.Text('Payment Terms:')
    appendix = fields.Text('Appendix:')
    voucher_date = fields.Date('Voucher Date')
    recived_partner_id = fields.Many2one('res.partner','Received from')
    sum_amount = fields.Char('The sum of')
    check_number = fields.Char('Cash / Cheque No  ')
    check_date = fields.Date('Date  ')
    the_for = fields.Char('For')
    number_of_de = fields.Char('NO')


    the_language = fields.Selection(string='The language it is written in',
                                    selection=[('ar', 'Arabic'), ('en', 'English')],
                                    )


    amount_due = fields.Float('Amount Due',store=True,copy=False)
    is_culcu = fields.Boolean()
    add_vat = fields.Boolean()
    add_with_out = fields.Boolean()
    show_photo = fields.Boolean('Dont Show Photo In report')
    is_new_order = fields.Boolean('Duplicate Quotations',copy=False)
    project_des = fields.Char('Project Description',default='')
    status_payment = fields.Selection([('1st', 'The first batch of the project'), ('2st', 'The second batch of the project')
                                          , ('3st', 'The third batch of the project ')
                                          , ('4st', 'The fourth batch of the project ')
                                          , ('5st', 'The remaining amount from the project ')
                                          , ('6st', 'Full project amount ')


                                       ], 'Project payments',)
    status_payment_vatue = fields.Selection([('percent', 'Percent '), ('amount', 'Amount')


                                       ], 'Payment Methods',)



    def get_items(self):
        print('items')

        for line in self.order_line:
            self.env['receipt.report'].create({
                'code' : line.product_template_id.name,
                'name' : line.name,
                'account' : line.product_uom_qty,
                'sale_id' : self.id,

            })

    def get_pay_percentage(self):
        if not self.status_payment_vatue == 'percent' and not self.status_payment_vatue == 'amount':
            raise UserError(
                _('You must choose the payment method, either a percentage or an amount'))
            print('errroes')

        vat_with_price = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', '15'),
                                               ('price_include', '=', False),('company_id', '=', self.company_id.id),

                                               ], limit=1)
        print(vat_with_price,'eeeeeeeeeee')
        vat_price = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', '15'),
                                               ('price_include', '=', True),('company_id', '=', self.company_id.id),
                                               ], limit=1)
        print(vat_price.company_id.id,'vate')
        # percentage = 0
        now = datetime.today().date()
        payment = ''
        if self.status_payment == '1st' :
            payment = 'الدفعة الأولي من المشروع '
        elif self.status_payment == '2st' :
            payment = 'الدفعة الثانية من المشروع '
        elif self.status_payment == '3st' :
            payment = 'الدفعة الثالثة من المشروع '
        elif self.status_payment == '4st' :
            payment = 'الدفعة الرابعة من المشروع '
        elif self.status_payment == '5st' :
            payment = 'باقي المبلغ من المشروع '
        else :
            payment = 'كامل مبلغ المشروع '
        for rec in self:

            if self.add_vat == True and self.status_payment_vatue =='percent':

                if rec.is_culcu == False:
                    rec.invoice_amount = (rec.amount_untaxed * rec.pay_percentage) / 100
                    if rec.invoice_amount == 0:
                        raise UserError(
                            _('The project amount has been paid in full ! Or there is no billing amount '))
                    print( rec.invoice_amount,'percentage')
                    # rec.invoice_amount = int(percentage)
                    if rec.invoice_amount > rec.amount_untaxed :

                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    rec.amount_due = rec.amount_untaxed - rec.invoice_amount
                    rec.is_culcu = True
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' :now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                        'name' : payment + str(' - ') + str(self.project_des) ,
                        'price_unit' : self.invoice_amount,
                        'quantity' : 1.0,
                        'tax_ids' : vat_with_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)


                    rec.pay_percentage = 0



                else:


                    print('True')
                    rec.invoice_amount = (rec.amount_due * rec.pay_percentage) / 100
                    if rec.invoice_amount == 0:
                        raise UserError(
                            _('The project amount has been paid in full !'))

                    print(rec.invoice_amount,'ttttttttttttt')
                    print(rec.amount_due)
                    if rec.invoice_amount > rec.amount_due:
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                                    'name': payment + str(' - ') + str(self.project_des) ,
                                    'price_unit' : self.invoice_amount,
                                    'quantity' : 1.0,
                                    'tax_ids' : vat_with_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    rec.amount_due = rec.amount_due - rec.invoice_amount
                    rec.pay_percentage = 0

            if self.add_vat == True and self.status_payment_vatue == 'amount':
                if rec.is_culcu == False :
                    rec.invoice_amount = rec.pay_percentage
                    if rec.invoice_amount == 0 :
                        raise UserError(
                            _('The project amount has been paid in full ! Or there is no billing amount '))
                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    if rec.invoice_amount > rec.amount_untaxed :
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    rec.amount_due = rec.amount_untaxed - rec.pay_percentage
                    rec.is_culcu = True
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                            'name' : payment + str(' - ') + str(self.project_des),
                            'price_unit' : self.invoice_amount,
                            'quantity' : 1.0,
                            'tax_ids' : vat_with_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    rec.pay_percentage = 0



                else :
                    print('True')
                    rec.invoice_amount = rec.pay_percentage
                    if rec.invoice_amount > self.amount_due :
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    print(rec.invoice_amount, 'ttttttttttttt')
                    print(rec.amount_due)
                    if rec.invoice_amount > rec.amount_due :
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))
                    invoice_vals = {
                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                            'name' : payment + str(' - ') + str(self.project_des),
                            'price_unit' : self.invoice_amount,
                            'quantity' : 1.0,
                            'tax_ids' : vat_with_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    rec.amount_due = rec.amount_due - rec.invoice_amount
                    rec.pay_percentage = 0


        ######################################################

            if self.add_with_out == True and self.status_payment_vatue =='percent':

                if rec.is_culcu == False:
                    rec.invoice_amount = (rec.amount_total * rec.pay_percentage) / 100
                    if rec.invoice_amount == 0:
                        raise UserError(
                            _('The project amount has been paid in full ! Or there is no billing amount '))
                    print( rec.invoice_amount,'percentage')
                    # rec.invoice_amount = int(percentage)
                    if rec.invoice_amount > rec.amount_untaxed :

                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    rec.amount_due = rec.amount_total - rec.invoice_amount
                    rec.is_culcu = True
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' :now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                        'name' : payment + str(' - ') + str(self.project_des) ,
                        'price_unit' : self.invoice_amount,
                        'quantity' : 1.0,
                        'tax_ids' : vat_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)


                    rec.pay_percentage = 0



                else:


                    print('True')
                    rec.invoice_amount = (rec.amount_due * rec.pay_percentage) / 100
                    if rec.invoice_amount == 0:
                        raise UserError(
                            _('The project amount has been paid in full !'))

                    print(rec.invoice_amount,'ttttttttttttt')
                    print(rec.amount_due)
                    if rec.invoice_amount > rec.amount_due:
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                        'name' :payment + str(' - ') + str(self.project_des) ,
                        'price_unit' : self.invoice_amount,
                        'quantity' : 1.0,
                        'tax_ids' : vat_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    rec.amount_due = rec.amount_total - rec.invoice_amount
                    rec.pay_percentage = 0

            if self.add_with_out == True and self.status_payment_vatue == 'amount':
                if rec.is_culcu == False :
                    rec.invoice_amount = rec.pay_percentage
                    if rec.invoice_amount == 0 :
                        raise UserError(
                            _('The project amount has been paid in full ! Or there is no billing amount '))
                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    if rec.invoice_amount > rec.amount_untaxed :
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    rec.amount_due = rec.amount_total - rec.pay_percentage
                    rec.is_culcu = True
                    invoice_vals = {

                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                            'name' : payment + str(' - ') + str(self.project_des),
                            'price_unit' : self.invoice_amount,
                            'quantity' : 1.0,
                            'tax_ids' : vat_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    rec.pay_percentage = 0



                else :
                    print('True')
                    rec.invoice_amount = rec.pay_percentage
                    if rec.invoice_amount > self.amount_due :
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))

                    print(rec.invoice_amount, 'ttttttttttttt')
                    print(rec.amount_due)
                    if rec.invoice_amount > rec.amount_due :
                        print('error')
                        raise UserError(
                            _('The process cannot be completed because the requested amount is greater than the due amount !'))
                    invoice_vals = {
                        'move_type' : 'out_invoice',
                        'partner_id' : self.partner_id.id,
                        'invoice_date_due' : now,
                        'invoice_date' : now,
                        'account_custom_id' : self.id,
                        'project_id' : self.project_id.id,
                        'invoice_line_ids' : [(0, 0, {
                            'name' : payment + str(' - ') + str(self.project_des),
                            'price_unit' : self.invoice_amount,
                            'quantity' : 1.0,
                            'tax_ids' : vat_price,

                        })],
                    }

                    invoice_id = self.env['account.move'].create(invoice_vals)

                    print(rec.invoice_amount, 'percentage')
                    # rec.invoice_amount = int(percentage)
                    rec.amount_due = rec.amount_due - rec.invoice_amount
                    rec.pay_percentage = 0

    def _get_report_base_filename_plient_appendix1(self) :
        self.ensure_one()
        return 'Quotations - %s' % (str(self.partner_id.name +' ' + self.name))

    def copy_record(self):
        new = self.copy()
        print('copy')

    def create_purchase(self):
        lines = []
        for rec in self.order_line:
            if rec.is_purchase:
                lines.append((0, 0, {
                    'product_id': rec.product_template_id.id,
                    'name': rec.name,
                    'product_qty': rec.product_uom_qty,

                }))
            purchase_vals = {

                    'partner_id': self.vendor_id.id,
                    'order_line': lines
                }

        invoice_id = self.env['purchase.order'].create(purchase_vals)

    def add_vate(self):
        self.add_vat = True
        self.add_with_out = False

        for rec in self :
            vats = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', '15'),
                                                       ('price_include', '=', False),
                                                   ('company_id', '=', self.company_id.id),
                                                       ],limit=1)
            print(vats.company_id)

            for vat in self.order_line :
                vat.tax_id = vats

    def add_with_vat(self):
        for rec in self :
            self.add_with_out = True
            self.add_vat = False
            vats = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', '15'),
                                                       ('price_include', '=', True),
                                                   ('company_id', '=', self.company_id.id),
                                                       ],limit=1)
            print(vats.company_id)

            for vat in self.order_line :
                vat.tax_id = vats


class SaleOrderLineCustom(models.Model):
    _inherit = 'sale.order.line'

    is_purchase = fields.Boolean('Purchase Order Line')
    name = fields.Text('Name',related='product_template_id.description_sale',readonly=False)
    description_sale = fields.Text('Description Sale',related='product_template_id.description_sale',readonly=False)
    barcode = fields.Char('Code',related='product_template_id.barcode',)



class producttemplate(models.Model):
    _inherit = 'product.template'


    prod_disc = fields.Char('Product Discraption')














