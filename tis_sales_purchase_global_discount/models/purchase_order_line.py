# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    amount_after_discount = fields.Float()

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            quantity=self.product_qty,
            price_subtotal=self.price_subtotal,
            discount_for=self.order_id.discount_for,
            discount_type=self.order_id.discount_type,
            discount_rate=self.order_id.discount_rate,
            discount_narration=self.order_id.discount_narration,
            discount_amount=self.order_id.amount_discount,
            amount_untaxed_before_global_discounts=self.order_id.amount_untaxed_before_global_discounts,
            count_line=len(self.order_id.order_line)
        )
