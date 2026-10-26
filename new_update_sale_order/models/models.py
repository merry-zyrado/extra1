from odoo import api, fields, models


class Salesorder(models.Model):
    _inherit = 'sale.order.line'

    name = fields.Text('Name', required=False)

    discount_amount = fields.Float(string='Discount Amount',)


    @api.onchange('discount_amount')
    @api.constrains('discount_amount')
    def _onchange_discount(self):
        for invoice in self:
            if invoice.discount_amount:
                invoice.discount = (invoice.discount_amount / (invoice.price_unit * invoice.product_uom_qty)) * 100
            else:
                invoice.discount = 0
