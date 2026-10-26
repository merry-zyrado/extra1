from odoo import api, fields, models,_


class PurcheaseCustom(models.Model):
    _inherit = 'purchase.order'

    custom_rate = fields.Float(string='Exchange Rate')
    total_rate = fields.Float('Total Rate',compute='_compute_total_rate')



    @api.depends('order_line')
    @api.onchange('order_line')
    def _compute_total_rate(self):
        total=0
        for rec in self.order_line:
            total += rec.exchangeـrate
        self.total_rate =total








    def cululate_rate(self):
        print('test')
        total = 0
        for rec in self.order_line:
            rec.exchangeـrate = rec.price_unit
            rec.price_unit = rec.exchangeـrate * self.custom_rate

        # for line in self.order_line:
        #     total += line.exchangeـrate
        #
        # self.total_rate =total









class purchaseOrdelLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    exchangeـrate = fields.Float(string='Exchange Rate')






