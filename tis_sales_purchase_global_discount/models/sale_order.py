# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo.addons import decimal_precision as dp

import json
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_untaxed_before_global_discounts = fields.Monetary(
        string="Amount Untaxed Before Discounts",
        compute="_compute_amounts",
        currency_field="currency_id",
        compute_sudo=True,
        readonly=True,
        store=True,
    )

    amount_total_before_global_discounts = fields.Monetary(
        string="Amount Total Before Discounts",
        compute="_compute_amounts",
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
                                   store=True, readonly=True, compute='_compute_amounts', track_visibility='always')
    amount_grand = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_compute_amounts', track_visibility='always')

    @api.model
    def get_discounted_global(self, price=0, discounts=None):
        """Compute discounts successively"""
        discounts = discounts or []
        if not discounts:
            return price
        discount = discounts.pop(0)
        price *= (1 - (discount / 100.0))
        return self.get_discounted_global(price, discounts)

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'discount_for',
                 'discount_type', 'discount_rate')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
            if self.discount_for == 'untaxed' and self.discount_rate > 0.0:
                if self.discount_type == 'percent':
                    discounts = [self.discount_rate]
                else:
                    if self.discount_rate > self.amount_untaxed:
                        raise UserError(_('Discount amount should not be greater than untaxed amount'))
                    discounts = [(self.discount_rate / self.amount_untaxed) * 100]
                price = self.get_discounted_global(price, discounts.copy())
            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(
                price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id,
                partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(
                order.order_line, compute_taxes)
            tax_totals = account_move._get_tax_totals(
                order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'discount_for',
                 'discount_type', 'discount_rate')
    def _compute_tax_totals(self):
        for order in self:
            price_total = []
            for rec in self.order_line:
                price = rec.product_uom_qty * rec.price_unit
                price_total.append(price)
                self.amount_untaxed_before_global_discounts = sum(price_total)
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id,
            )

    def get_tax_excluded_price(self):
        sum_price = []
        for rec in self.order_line:
            if self.discount_type == "percent":
                price = rec.product_uom_qty * rec.price_unit
                discounts = self.discount_rate
                price *= (1 - (discounts / 100.0))
                sum_price.append(price)
            else:
                if self.discount_rate > self.amount_untaxed:
                    raise UserError(_('Discount amount should not be greater than untaxed amount'))
                price = rec.product_uom_qty * rec.price_unit
                discounts = (self.discount_rate / self.amount_untaxed) * 100
                price *= (1 - (discounts / 100.0))
                sum_price.append(price)
        self.amount_untaxed_before_global_discounts = self.amount_untaxed
        return self.amount_untaxed - sum(sum_price)

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total', 'amount_untaxed',
                 'amount_total', 'amount_tax', 'discount_type', 'discount_rate', 'discount_for', 'order_line.tax_id',
                 'order_line.product_id')
    def _compute_amounts(self):
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

            order.amount_untaxed_before_global_discounts = order.amount_untaxed
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
                    line.amount_after_discount = discounted_subtotal
                    amount_discounted_untaxed += discounted_subtotal
                    discounted_tax = line.tax_id.compute_all(
                        discounted_subtotal,
                        line.order_id.currency_id,
                        1.0,
                        product=line.product_id,
                        partner=line.order_id.partner_shipping_id,
                    )
                    amount_discounted_tax += sum(
                        t.get("amount", 0.0) for t in discounted_tax.get("taxes", [])
                    )
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
                            'amount_total': order.tax_totals.get('amount_total')
                        })
            elif order.discount_for == 'total' and order.discount_rate > 0.0:
                order.amount_untaxed_before_global_discounts = self.amount_untaxed
                round_curr = order.currency_id.round
                order.amount_grand = order.amount_untaxed + order.amount_tax
                if order.discount_type == "percent":
                    if order.currency_id:
                        order.amount_discount = round_curr(order.amount_grand * order.discount_rate / 100) * -1
                    else:
                        raise UserError(
                            _("Please select a pricelists"))
                elif order.discount_type == "amount":
                    if order.currency_id:
                        order.amount_discount = round_curr(order.discount_rate) * -1
                    else:
                        raise UserError(
                            _("Please select a pricelists"))

                if order.amount_grand >= order.amount_discount:
                    order.amount_total = order.amount_grand + order.amount_discount

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'discount_for': self.discount_for,
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
            'discount_narration': self.discount_narration,
        })
        return res
