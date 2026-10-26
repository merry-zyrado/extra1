from odoo import api, fields, models

class Sales_order_inharet(models.Model):
    _inherit = 'sale.order'

    def get_items(self):
        res = super().get_items()  # Call the original method
        print('Extended get_items logic')

        for line in self.order_line:
            product = line.product_id

            self.env['receipt.report'].create({
                'code': line.product_template_id.name,
                'name': line.name,
                'product_code': line.product_template_id.barcode,
                'account': line.product_uom_qty,
                'sale_id': self.id,
            })

        return res



class receiptreport(models.Model):
    _inherit = 'receipt.report'

    product_code = fields.Char(string='Product Code')



