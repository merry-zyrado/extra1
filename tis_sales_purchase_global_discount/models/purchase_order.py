# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import json


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    amount_untaxed_before_global_discounts = fields.Monetary(
        string="Amount Untaxed Before Discounts",
        compute="_amount_all",
        currency_field="currency_id",
        compute_sudo=True,
        readonly=True,
        store=True,
    )

    amount_total_before_global_discounts = fields.Monetary(
        string="Amount Total Before Discounts",
        compute="_amount_all",
        currency_field="currency_id",
        compute_sudo=True,
        readonly=True,
        store=True,
    )

    discount_for = fields.Selection(string='Discount For',
                                    selection=[('total', 'Total'), ('untaxed', 'Untaxed')], readonly=True,
                                    states={'draft': [('readonly', False)]})
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                  readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'),
                                   store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_grand = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_total = fields.Float(string='Net Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_amount_all')

    @api.model
    def get_discounted_global(self, price=0, discounts=None):
        discounts = discounts or []
        if not discounts:
            return price
        discount = discounts.pop(0)
        price *= 1 - (discount / 100)
        return self.get_discounted_global(price, discounts)

    def get_tax_excluded_price(self):
        sum_price = []
        sum_price_disc = []
        for rec in self.order_line:
            if self.discount_type == "percent":
                price = rec.product_uom_qty * rec.price_unit
                sum_price.append(price)
                discounts = self.discount_rate
                price *= (1 - (discounts / 100.0))
                sum_price_disc.append(price)
            else:
                if self.discount_rate > self.amount_untaxed:
                    raise UserError(_('Discount amount should not be greater than untaxed amount'))
                price = rec.product_uom_qty * rec.price_unit
                sum_price.append(price)
                discounts = (self.discount_rate / self.amount_untaxed) * 100

                price *= (1 - (discounts / 100.0))
                sum_price_disc.append(price)
        return sum(sum_price) - sum(sum_price_disc)

    @api.depends('discount_type', 'discount_rate', 'discount_for')
    def _amount_all(self):
        # res = super(PurchaseOrder, self)._amount_all()
        for order in self:
            order_lines = order.order_line.filtered(
                lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get(
                    'amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get(
                    'amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + order.amount_tax

            if order.discount_for == 'untaxed' and order.discount_rate > 0.0:
                amount_untaxed_before_global_discounts = order.amount_untaxed
                amount_total_before_global_discounts = order.amount_total
                if order.discount_type == 'percent':
                    discounts = [order.discount_rate]
                else:
                    sum_price = []
                    for rec in self.order_line:
                        price = rec.product_uom_qty * rec.price_unit
                        sum_price.append(price)
                    if sum_price:
                        if order.discount_rate > sum(sum_price):
                            raise UserError(_('Discount amount should not be greater than untaxed amount'))
                        discounts = [(order.discount_rate / sum(sum_price)) * 100]
                amount_discounted_untaxed = amount_discounted_tax = 0
                for line in order.order_line:
                    discounted_subtotal = order.get_discounted_global(
                        line.price_subtotal, discounts.copy()
                    )
                    if line.order_id.discount_type == 'percent':
                        count = len(line.order_id.order_line)
                        line_discount = line.order_id.discount_rate
                        line_discount_price_per = line.price_subtotal * (line_discount / 100)
                        line_discount_price = line.price_subtotal - line_discount_price_per
                        line.amount_after_discount = line_discount_price / line.product_qty
                    elif line.order_id.discount_type == 'amount':
                        count = len(line.order_id.order_line)
                        line_discount = line.order_id.discount_rate / count
                        line_discount_price = line.price_subtotal - line_discount
                        line.amount_after_discount = line_discount_price / line.product_qty
                    amount_discounted_untaxed += discounted_subtotal
                order.update(
                    {
                        "amount_untaxed_before_global_discounts": (
                            amount_untaxed_before_global_discounts
                        ),
                        "amount_discount": (
                                                   amount_untaxed_before_global_discounts
                                                   - amount_discounted_untaxed
                                           ) * -1,
                    }
                )
                if order.tax_totals:
                    if not order.tax_totals['groups_by_subtotal'].get('Untaxed Amount'):
                        order.update({
                            'amount_total': (order.amount_untaxed + order.amount_discount)
                        })
                        order.amount_total = (order.amount_untaxed + order.amount_discount)
                    else:
                        order.update({
                            'amount_total': (
                                    order.tax_totals[
                                        'groups_by_subtotal'].get(
                                        'Untaxed Amount')[0].get(
                                        'tax_group_amount') +
                                    order.tax_totals[
                                        'groups_by_subtotal'].get(
                                        'Untaxed Amount')[0].get(
                                        'tax_group_base_amount'))
                        })
                        order.amount_total = (order.tax_totals.get('amount_total')

                                              )
            elif order.discount_for == 'total' and order.discount_rate > 0.0:
                order.amount_untaxed_before_global_discounts = self.amount_untaxed
                round_curr = order.currency_id.round
                order.amount_grand = order.amount_untaxed + order.amount_tax
                if order.discount_type == "percent":
                    order.amount_discount = round_curr(order.amount_grand * order.discount_rate / 100) * -1
                elif order.discount_type == "amount":
                    order.amount_discount = round_curr(order.discount_rate) * -1
                if (order.amount_grand >= order.amount_discount):
                    order.amount_total = order.amount_grand + order.amount_discount
        # return res

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res.update({
            'discount_for': self.discount_for,
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
            'discount_narration': self.discount_narration,
        })
        return res

    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for order in self:
            order.amount_untaxed_before_global_discounts = order.amount_untaxed
            order.amount_total_before_global_discounts = order.amount_total
