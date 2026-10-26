from odoo import api, fields, models


class Purcheaseordercussdtom(models.Model):
    _inherit = 'purchase.order'

    payment_terms = fields.Text('Payment Terms:')
    shipping_terms = fields.Text('Shipping Terms:')
    delivery_date = fields.Date('Delivery Date:')
    comments = fields.Text('Comments or Special Instructions')
    consignee_id = fields.Many2one('res.partner', string='CONSIGNEE TO', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                             )

    invoice_to_id = fields.Many2one('res.partner', string='INVOICE TO', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                              )




