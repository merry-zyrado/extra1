# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, Command, _
from odoo.tools import frozendict

INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    display_type = fields.Selection(selection_add=[('global_discount', 'Global Discount')],
                                    ondelete={'global_discount': 'cascade'})
    discount_dirty = fields.Boolean(compute='_compute_discount_needed')
    discount_needed = fields.Binary(compute='_compute_discount_needed')

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1

        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit if is_invoice else self.amount_currency,
            quantity=self.quantity if is_invoice else 1.0,
            discount=self.discount if is_invoice else 0.0,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            price_subtotal=sign * self.amount_currency,
            is_refund=self.is_refund,
            rate=(abs(self.amount_currency) / abs(self.balance)) if self.balance else 1.0,
            discount_for=self.move_id.discount_for,
            discount_type=self.move_id.discount_type,
            discount_rate=self.move_id.discount_rate,
            discount_narration=self.move_id.discount_narration,
            discount_amount=self.move_id.amount_discount,
            amount_untaxed_before_global_discounts=self.move_id.amount_untaxed_before_global_discounts,
            count_line=len(self.move_id.invoice_line_ids)

        )

    @api.depends('move_id.needed_terms', 'account_id', 'analytic_distribution', 'tax_ids', 'tax_tag_ids', 'company_id',
                 'product_id', "move_id.discount_rate", "move_id.discount_type", "move_id.discount_for")
    def _compute_discount_needed(self):
        for line in self:
            line.discount_dirty = True
            line.discount_needed = False
            global_discount_needed = {}
        if self[-1].move_type=='in_invoice':
            amount_currency= self.move_id.amount_discount
            credit = self.move_id.amount_discount > 0.0 and self.move_id.amount_discount or 0.0
            debit = 0.0
        else:
            amount_currency= -self.move_id.amount_discount
            credit = 0.0
            debit = self.move_id.amount_discount > 0.0 and self.move_id.amount_discount or 0.0
        if self.filtered(lambda l: l.display_type == 'global_discount'):
            for rec in self.filtered(lambda l: l.display_type == 'global_discount'):
                rec.amount_currency = amount_currency
        else:
            existed = False
            if self.move_id.line_ids.filtered(lambda l: l.display_type == 'global_discount'):
                existed = True
            if not existed:
                sale_discount_account = self.company_id.account_def_discount_sales_account_id.id
                epd_needed_vals = global_discount_needed.setdefault(
                    frozendict({
                        'move_id': self[-1].move_id.id,
                        'account_id': sale_discount_account,
                        'analytic_distribution': self[-1].analytic_distribution,
                        'display_type': 'global_discount',
                    }),
                    {
                        'name': "Global Discount",
                        'amount_currency': amount_currency,
                    },
                )
                self[-1].discount_needed = {k: frozendict(v) for k, v in global_discount_needed.items()}
        return

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id',
                 'move_id.partner_id', 'price_unit','move_id.discount_rate')
    def _compute_all_tax(self):
        if self.env.context.get('active_model') == 'hr.expense':
            return super(AccountMoveLine, self)._compute_all_tax()
        else:
            for line in self:
                sign = line.move_id.direction_sign
                if line.display_type == 'tax':
                    line.compute_all_tax = {}
                    line.compute_all_tax_dirty = False
                    continue
                if line.display_type == 'product' and line.move_id.is_invoice(True):
                    if line.move_id.discount_for == 'untaxed':
                        if line.move_id.discount_type == 'amount':
                            count = 0
                            for move_line in line.move_id.line_ids:
                                if move_line.display_type == 'product':
                                    count = count+1
                            discounts = line.move_id.discount_rate / (line.quantity * line.price_unit) * 100
                            discounts = discounts / count
                        else:
                            discounts = line.move_id.discount_rate
                        amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                        amount_currency = (amount_currency - (amount_currency * discounts) / 100)
                    else:
                        amount_currency = sign * line.price_unit * (1 - line.discount / 100)

                    handle_price_include = True
                    quantity = line.quantity
                else:
                    amount_currency = line.amount_currency
                    handle_price_include = False
                    quantity = 1
                compute_all_currency = line.tax_ids.compute_all(
                    amount_currency,
                    currency=line.currency_id,
                    quantity=quantity,
                    product=line.product_id,
                    partner=line.move_id.partner_id or line.partner_id,
                    is_refund=line.is_refund,
                    handle_price_include=handle_price_include,
                    include_caba_tags=line.move_id.always_tax_exigible,
                    fixed_multiplicator=sign,
                )
                rate = line.amount_currency / line.balance if line.balance else 1
                line.compute_all_tax_dirty = True
                line.compute_all_tax = {
                    frozendict({
                        'tax_repartition_line_id': tax['tax_repartition_line_id'],
                        'group_tax_id': tax['group'] and tax['group'].id or False,
                        'account_id': tax['account_id'] or line.account_id.id,
                        'currency_id': line.currency_id.id,
                        'analytic_distribution': (tax['analytic'] or not tax[
                            'use_in_tax_closing']) and line.analytic_distribution,
                        'tax_ids': [(6, 0, tax['tax_ids'])],
                        'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                        'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                        'move_id': line.move_id.id,
                    }): {
                        'name': tax['name'],
                        'balance': tax['amount'] / rate,
                        'amount_currency': tax['amount'],
                        'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                    }
                    for tax in compute_all_currency['taxes']
                    if tax['amount']
                }
                if not line.tax_repartition_line_id:
                    line.compute_all_tax[frozendict({'id': line.id})] = {
                        'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                    }