# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from contextlib import ExitStack, contextmanager
from odoo.tools import (frozendict)
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    is_html_empty,
    sql
)

class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_for = fields.Selection(string='Discount For',
                                    selection=[('total', 'Total'), ('untaxed', 'Untaxed')],
                                    states={'draft': [('readonly', False)]})
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount', track_visibility='always')
    amount_untaxed_before_global_discounts = fields.Monetary(
        string="Amount Untaxed Before Discounts",
        compute="_compute_amount",
        currency_field="currency_id",
        readonly=True,
        compute_sudo=True,
        store=True,
    )
    amount_grand = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                  readonly=True, states={'draft': [('readonly', False)]})
    total_disc_amount = fields.Monetary(
        string='total_disc_amount',
        compute='_compute_amount', store=True,
        help="The residual amount on a journal item expressed in the company currency.",
    )

    @api.onchange("discount_rate", "discount_type", "discount_for")
    def _onchange_global_discount(self):
        sale_discount_account = self.company_id.account_def_discount_sales_account_id.id
        purchase_discount_account = self.company_id.account_def_discount_purchase_account_id.id
        if not sale_discount_account or not purchase_discount_account:
            raise UserError(
                _('Please Configure Sales & Purchase Discount Account.'))

    def _recompute_tax_lines(
            self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None
    ):
        if not recompute_tax_base_amount:
            self.line_ids -= self.line_ids.filtered("global_discount_item")
        res = super()._recompute_tax_lines(
            recompute_tax_base_amount,
            tax_rep_lines_to_recompute=tax_rep_lines_to_recompute,
        )
        if not recompute_tax_base_amount and self.discount_for == 'untaxed':
            self._update_tax_lines_for_global_discount()
            self._set_global_discounts_by_tax()
            self._recompute_global_discount_lines()
        if not recompute_tax_base_amount and self.discount_for == 'total':
            self._recompute_global_discount_total_lines()
        return res

    def _recompute_global_discount_total_lines(self):
        ''' Recompute the global discount line'''
        self.ensure_one()
        self = self.with_company(self.company_id)
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_company(self.journal_id.company_id)

        existing_global_discount_line = self.line_ids.filtered(
            lambda line: line.global_discount_item)
        others_lines = self.line_ids.filtered(
            lambda line: not line.global_discount_item)

        if not others_lines:
            self.line_ids -= existing_global_discount_line
            return

        if self.discount_type == 'percent':
            global_discount = self.amount_grand * self.discount_rate / 100
        else:
            global_discount = self.discount_rate
        if not global_discount:
            self.line_ids -= existing_global_discount_line
            return

        if existing_global_discount_line.debit == -global_discount:
            return

        new_global_discount_line = self.env['account.move.line']
        if self.move_type in {"out_invoice", "out_refund"}:
            account = - self.company_id.account_def_discount_sales_account_id
            credit = 0.0
            debit = global_discount > 0.0 and global_discount or 0.0
        elif self.move_type in {"in_invoice", "in_refund"}:
            account = self.company_id.account_def_discount_purchase_account_id
            credit = global_discount < 0.0 and -global_discount or 0.0
            debit = 0.0
        if existing_global_discount_line:
            existing_global_discount_line.update({
                "amount_currency": -global_discount,
                "debit": debit,
                "credit": credit,
            })
        else:
            if not self.company_id.account_def_discount_sales_account_id:
                raise UserError(
                    _("Please Configure Sales Discount Account."))
            create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
            candidate = create_method({
                'name': 'Global Discount',
                "debit": debit,
                "credit": credit,
                'quantity': 1.0,
                'amount_currency': -global_discount,
                'move_id': self.id,
                'date_maturity': today,
                'currency_id': self.currency_id.id,
                'account_id': account.id,
                'partner_id': self.commercial_partner_id.id,
                'global_discount_item': True,
                'exclude_from_invoice_tab': True,
            })
            new_global_discount_line += candidate
            if in_draft_mode:
                candidate.update(candidate._get_fields_onchange_balance(force_computation=True))
        if not existing_global_discount_line:
            self.line_ids -= existing_global_discount_line - new_global_discount_line

    def _update_tax_lines_for_global_discount(self):
        round_curr = self.currency_id.round
        tax_lines = self.line_ids.filtered(
            lambda r: r.tax_line_id.amount_type in ("percent", "division")
        )
        for tax_line in tax_lines:
            base = tax_line.tax_base_amount
            tax_line.base_before_global_discounts = base
            amount = tax_line.balance
            if self.discount_type == 'percent':
                base = base * (1 - (self.discount_rate / 100))
                amount = amount * (1 - (self.discount_rate / 100))
            else:
                if self.discount_rate > self.amount_untaxed_before_global_discounts:
                    raise UserError(_("Discount amount can't be greater than untaxed amount."))
                discount_rate = (self.discount_rate / self.amount_untaxed_before_global_discounts) * 100
                base = base * (1 - (discount_rate / 100))
                amount = amount * (1 - (discount_rate / 100))
            tax_line.tax_base_amount = round_curr(base)
            tax_line.debit = amount > 0.0 and amount or 0.0
            tax_line.credit = amount < 0.0 and -amount or 0.0
            tax_line._onchange_balance()
            tax_line._onchange_amount_currency()

    def _set_global_discounts_by_tax(self):
        self.ensure_one()
        if not self.is_invoice():
            return
        taxes_keys = {}
        _self = self.filtered("discount_rate")
        for inv_line in _self.invoice_line_ids.filtered(lambda l: not l.display_type):
            for key in taxes_keys:
                if key == tuple(inv_line.tax_ids.ids):
                    break
            else:
                taxes_keys[tuple(inv_line.tax_ids.ids)] = True
        for tax_line in _self.line_ids.filtered("tax_line_id"):
            key = []
            to_create = True
            for key in taxes_keys:
                if tax_line.tax_line_id.id in key:
                    to_create = taxes_keys[key]
                    taxes_keys[key] = False  # mark for not duplicating
                    break  # we leave in key variable the proper taxes value
            if not to_create:
                continue

    def _recompute_global_discount_lines(self):
        self.ensure_one()
        in_draft_mode = self != self._origin
        model = "account.move.line"
        create_method = in_draft_mode and self.env[model].new or self.env[model].create
        discount = self.amount_discount
        sign = -1 if self.move_type in {"in_invoice", "out_refund"} else 1
        disc_amount = sign * discount
        if self.move_type in {"out_invoice", "out_refund"}:
            account = self.company_id.account_def_discount_sales_account_id
            credit = 0.0
            debit = disc_amount > 0.0 and disc_amount or 0.0
        elif self.move_type in {"in_invoice", "in_refund"}:
            account = self.company_id.account_def_discount_purchase_account_id
            credit = disc_amount < 0.0 and -disc_amount or 0.0
            debit = 0.0
        create_method(
            {
                "global_discount_item": True,
                "move_id": self.id,
                "name": "Discount",
                "debit": debit,
                "credit": credit,
                "amount_currency": (disc_amount > 0.0 and disc_amount or 0.0)
                                   - (disc_amount < 0.0 and -disc_amount or 0.0),
                "account_id": account.id,
                "exclude_from_invoice_tab": True,
                "partner_id": self.commercial_partner_id.id,
            }
        )

    @api.model
    def get_discounted_global(self, price=0, discounts=None):
        discounts = discounts or []
        if not discounts:
            return price
        discount = discounts.pop(0)
        price *= 1 - (discount / 100)
        return self.get_discounted_global(price, discounts)

    @api.onchange("discount_rate", "discount_type", "discount_for")
    def _onchange_discount_params(self):
        if self.env.context.get('active_model') == 'hr.expense':
            self.amount_discount = 0.0
        else:
            sum_total = []
            for rec in self.invoice_line_ids:
                sum_total.append(rec.quantity * rec.price_unit)
            self.amount_untaxed_before_global_discounts = sum(sum_total)
            round_curr = self.currency_id.round
            if self.discount_for == "untaxed" and self.discount_rate > 0:
                sum_total = []
                for rec in self.invoice_line_ids:
                    sum_total.append(rec.quantity * rec.price_unit)
                self.amount_untaxed_before_global_discounts = sum(sum_total)
                if self.discount_type == "percent":
                    self.amount_discount = -round_curr(
                        self.amount_untaxed_before_global_discounts * self.discount_rate / 100)
                elif self.discount_type == "amount":
                    self.amount_discount = -round_curr(self.discount_rate)
                self.amount_untaxed = self.amount_untaxed - self.amount_discount
                self.amount_total = self.amount_untaxed + self.amount_tax
                if self.tax_totals:
                    if not self.tax_totals['groups_by_subtotal'].get('Untaxed Amount'):
                        self.update({
                            'amount_total': (self.amount_untaxed + self.amount_discount)
                        })
                        self.amount_total = (self.amount_untaxed + self.amount_discount)
                    else:
                        self.update({
                            'amount_total': self.tax_totals.get('amount_total')
                        })

                        self.amount_total = (self.tax_totals.get('amount_total'))
                amount_untaxed_signed = self.amount_untaxed
                if (
                        self.currency_id
                        and self.company_id
                        and self.currency_id != self.company_id.currency_id
                ):
                    date = self.invoice_date or fields.Date.today()
                    amount_untaxed_signed = self.currency_id._convert(
                        self.amount_untaxed, self.company_id.currency_id, self.company_id, date
                    )

                sign = self.move_type in ["in_invoice", "out_refund"] and -1 or 1
                self.amount_total_signed = self.amount_total * sign
                self.amount_untaxed_signed = amount_untaxed_signed * sign
            elif self.discount_for == "total" and self.discount_rate > 0:
                self.amount_grand = sum(self.invoice_line_ids.mapped("price_total"))
                if self.discount_type == "percent":
                    self.amount_discount = round_curr(self.amount_grand * self.discount_rate / 100) * -1
                elif self.discount_type == "amount":
                    self.amount_discount = round_curr(self.discount_rate) * -1
                if self.amount_grand >= self.amount_discount:
                    self.amount_total = self.amount_grand + self.amount_discount
                self.amount_untaxed = self.amount_untaxed - self.amount_discount
                self.amount_total = self.amount_untaxed + self.amount_tax
                amount_untaxed_signed = self.amount_untaxed
                if (
                        self.currency_id
                        and self.company_id
                        and self.currency_id != self.company_id.currency_id
                ):
                    date = self.invoice_date or fields.Date.today()
                    amount_untaxed_signed = self.currency_id._convert(
                        self.amount_untaxed, self.company_id.currency_id, self.company_id, date
                    )
                sign = self.move_type in ["in_invoice", "out_refund"] and -1 or 1
                self.amount_total_signed = self.amount_total * sign
                self.amount_untaxed_signed = amount_untaxed_signed * sign

            else:
                self.amount_discount = 0.0

    @api.depends(
        'discount_type', 'discount_for', 'invoice_line_ids.product_id',
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'discount_rate',
        'amount_discount')
    def _compute_amount(self):
        if self.env.context.get('active_model') == 'hr.expense':
            for move in self:
                total_untaxed, total_untaxed_currency = 0.0, 0.0
                total_tax, total_tax_currency = 0.0, 0.0
                total_residual, total_residual_currency = 0.0, 0.0
                total, total_currency = 0.0, 0.0

                for line in move.line_ids:
                    if move.is_invoice(True):
                        # === Invoices ===
                        if line.display_type == 'tax' or (
                                line.display_type == 'rounding' and line.tax_repartition_line_id):
                            # Tax amount.
                            total_tax += line.balance
                            total_tax_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                        elif line.display_type in ('product', 'rounding'):
                            # Untaxed amount.
                            total_untaxed += line.balance
                            total_untaxed_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                        elif line.display_type == 'payment_term':
                            # Residual amount.
                            total_residual += line.amount_residual
                            total_residual_currency += line.amount_residual_currency
                    else:
                        # === Miscellaneous journal entry ===
                        if line.debit:
                            total += line.balance
                            total_currency += line.amount_currency

                sign = move.direction_sign
                move.amount_untaxed = sign * total_untaxed_currency
                move.amount_tax = sign * total_tax_currency
                move.amount_total = sign * total_currency
                move.amount_residual = -sign * total_residual_currency
                move.amount_untaxed_signed = -total_untaxed
                move.amount_tax_signed = -total_tax
                move.amount_total_signed = abs(
                    total) if move.move_type == 'entry' else -total
                move.amount_residual_signed = total_residual
                move.amount_total_in_currency_signed = abs(
                    move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)
        else:
            for move in self:
                total_untaxed, total_untaxed_currency = 0.0, 0.0
                total_tax, total_tax_currency = 0.0, 0.0
                total_residual, total_residual_currency, total_disc_amount = 0.0, 0.0, 0.0
                total, total_currency = 0.0, 0.0
                for line in move.line_ids:
                    if move.is_invoice(True):
                        if line.display_type == 'tax' or (
                                line.display_type == 'rounding' and line.tax_repartition_line_id):
                            total_tax += line.balance
                            total_tax_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                        elif line.display_type == 'global_discount':
                            total_disc_amount += line.balance
                        elif line.display_type in ('product', 'rounding'):
                            total_untaxed += line.balance
                            total_untaxed_currency += line.amount_currency
                            total += line.balance
                            total_currency += line.amount_currency
                        elif line.display_type == 'payment_term':
                            total_residual += line.amount_residual
                            total_residual_currency += line.amount_residual_currency
                    else:
                        if line.debit:
                            total += line.balance
                            total_currency += line.amount_currency
                sign = move.direction_sign
                move.amount_untaxed = sign * total_untaxed_currency
                move.amount_tax = sign * total_tax_currency
                move.amount_total = sign * total_currency
                move.amount_residual = -sign * total_residual_currency
                move.amount_untaxed_signed = -total_untaxed
                move.amount_tax_signed = -total_tax
                move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
                move.amount_residual_signed = total_residual
                move.total_disc_amount = total_disc_amount
                move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)
                move.amount_untaxed_before_global_discounts = sign * total_untaxed_currency
        for record in self:
            record._onchange_discount_params()

    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=False, target=False) as disabled:
            yield
            if disabled:
                return

        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves:
            error_msg = _("An error has occurred.")
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "The move (%s) is not balanced.\n"
                    "The total of debits equals %s and the total of credits equals %s.\n"
                    "You might want to specify a default account on journal \"%s\" to automatically balance each move.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            raise UserError(error_msg)

    @contextmanager
    def _sync_dynamic_lines(self, container):
        if self.env.context.get('active_model') == 'hr.expense':
            with self._disable_recursion(container,
                                         'skip_invoice_sync') as disabled:
                if disabled:
                    yield
                    return

                def update_containers():
                    # Only invoice-like and journal entries in "auto tax mode" are synced
                    tax_container['records'] = container['records'].filtered(
                        lambda m: (m.is_invoice(
                            True) or m.line_ids.tax_ids and not m.tax_cash_basis_origin_move_id))
                    invoice_container['records'] = container[
                        'records'].filtered(lambda m: m.is_invoice(True))
                    misc_container['records'] = container['records'].filtered(
                        lambda
                            m: m.move_type == 'entry' and not m.tax_cash_basis_origin_move_id)

                tax_container, invoice_container, misc_container = ({} for __
                                                                    in
                                                                    range(3))
                update_containers()
                with ExitStack() as stack:
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='term_key',
                        needed_vals_fname='needed_terms',
                        needed_dirty_fname='needed_terms_dirty',
                        line_type='payment_term',
                        container=invoice_container,
                    ))
                    stack.enter_context(
                        self._sync_unbalanced_lines(misc_container))
                    stack.enter_context(
                        self._sync_rounding_lines(invoice_container))
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='tax_key',
                        needed_vals_fname='line_ids.compute_all_tax',
                        needed_dirty_fname='line_ids.compute_all_tax_dirty',
                        line_type='tax',
                        container=tax_container,
                    ))
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='epd_key',
                        needed_vals_fname='line_ids.epd_needed',
                        needed_dirty_fname='line_ids.epd_dirty',
                        line_type='epd',
                        container=invoice_container,
                    ))
                    stack.enter_context(self._sync_invoice(invoice_container))
                    line_container = {'records': self.line_ids}
                    with self.line_ids._sync_invoice(line_container):
                        yield
                        line_container['records'] = self.line_ids
                    update_containers()
        else:
            with self._disable_recursion(container, 'skip_invoice_sync') as disabled:
                if disabled:
                    yield
                    return
                tax_filter = lambda m: (
                        m.is_invoice(True) or m.line_ids.tax_ids and not m.tax_cash_basis_origin_move_id)
                invoice_filter = lambda m: (m.is_invoice(True))
                misc_filter = lambda m: (m.move_type == 'entry' and not m.tax_cash_basis_origin_move_id)
                tax_container = {'records': container['records'].filtered(tax_filter)}
                invoice_container = {'records': container['records'].filtered(invoice_filter)}
                misc_container = {'records': container['records'].filtered(misc_filter)}
                with ExitStack() as stack:
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='term_key',
                        needed_vals_fname='needed_terms',
                        needed_dirty_fname='needed_terms_dirty',
                        line_type='payment_term',
                        container=invoice_container,
                    ))
                    stack.enter_context(self._sync_unbalanced_lines(misc_container))
                    stack.enter_context(self._sync_rounding_lines(invoice_container))
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='tax_key',
                        needed_vals_fname='line_ids.compute_all_tax',
                        needed_dirty_fname='line_ids.compute_all_tax_dirty',
                        line_type='tax',
                        container=tax_container,
                    ))
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='epd_key',
                        needed_vals_fname='line_ids.discount_needed',
                        needed_dirty_fname='line_ids.discount_dirty',
                        line_type='global_discount',
                        container=invoice_container,
                    ))
                    stack.enter_context(self._sync_dynamic_line(
                        existing_key_fname='epd_key',
                        needed_vals_fname='line_ids.epd_needed',
                        needed_dirty_fname='line_ids.epd_dirty',
                        line_type='epd',
                        container=invoice_container,
                    ))
                    stack.enter_context(self._sync_invoice(invoice_container))
                    line_container = {'records': self.line_ids}
                    with self.line_ids._sync_invoice(line_container):
                        yield
                        line_container['records'] = self.line_ids
                    tax_container['records'] = container['records'].filtered(tax_filter)
                    invoice_container['records'] = container['records'].filtered(invoice_filter)
                    misc_container['records'] = container['records'].filtered(misc_filter)

                for move in container['records']:
                    if move.move_type == 'entry' and not move.line_ids.tax_ids:
                        move.line_ids.filtered(
                            lambda l: l.display_type == 'tax'
                        ).with_context(dynamic_unlink=True).unlink()

    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'discount_rate'
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()

    @api.depends('invoice_payment_term_id', 'invoice_date', 'currency_id', 'amount_total_in_currency_signed',
                 'invoice_date_due')
    def _compute_needed_terms(self):
        if self.env.context.get('active_model') == 'hr.expense':
            super()._compute_needed_terms()
            for move in self:
                if move.expense_sheet_id:
                    amount_currency = -sum(move.line_ids.filtered(
                        lambda l: l.display_type != 'payment_term').mapped(
                        "amount_currency"))
                    move.needed_terms = {
                        frozendict(
                            {
                                "move_id": move.id,
                                "date_maturity": move.expense_sheet_id.accounting_date
                                                 or fields.Date.context_today(
                                    move.expense_sheet_id),
                            }
                        ): {
                            "balance": amount_currency,
                            "amount_currency": amount_currency,
                            "name": "",
                            "account_id":
                                move.expense_sheet_id.expense_line_ids[
                                    0]._get_expense_account_destination(),
                        }
                    }
        else:
            for invoice in self:
                invoice.needed_terms = {}
                invoice.needed_terms_dirty = True
                sign = 1 if invoice.is_inbound(include_receipts=True) else -1
                if invoice.is_invoice(True):
                    if invoice.invoice_payment_term_id:
                        invoice_payment_terms = invoice.invoice_payment_term_id._compute_terms(
                            date_ref=invoice.invoice_date or invoice.date or fields.Date.today(),
                            currency=invoice.currency_id,
                            tax_amount_currency=invoice.amount_tax * sign,
                            tax_amount=invoice.amount_tax_signed,
                            untaxed_amount_currency=invoice.amount_untaxed * sign,
                            untaxed_amount=invoice.amount_untaxed_signed,
                            company=invoice.company_id,
                            sign=sign
                        )
                        for term in invoice_payment_terms:
                            key = frozendict({
                                'move_id': invoice.id,
                                'date_maturity': fields.Date.to_date(term.get('date')),
                                'discount_date': term.get('discount_date'),
                                'discount_percentage': term.get('discount_percentage'),
                            })
                            if invoice.move_type == "in_invoice" and invoice.purchase_order_count == 0:
                                values = {
                                    'balance': term['company_amount'],
                                    'amount_currency': term['foreign_amount'] - invoice.total_disc_amount,
                                    'name': invoice.payment_reference or '',
                                    'discount_amount_currency': term['discount_amount_currency'] or 0.0,
                                    'discount_balance': term['discount_balance'] or 0.0,
                                    'discount_date': term['discount_date'],
                                    'discount_percentage': term['discount_percentage'],
                                }
                            else:
                                values = {
                                    'balance': term['company_amount'],
                                    'amount_currency': term['foreign_amount'] - 2 * invoice.total_disc_amount,
                                    'name': invoice.payment_reference or '',
                                    'discount_amount_currency': term['discount_amount_currency'] or 0.0,
                                    'discount_balance': term['discount_balance'] or 0.0,
                                    'discount_date': term['discount_date'],
                                    'discount_percentage': term['discount_percentage'],
                                }
                            if key not in invoice.needed_terms:
                                invoice.needed_terms[key] = values
                            else:
                                invoice.needed_terms[key]['balance'] += values['balance']
                                invoice.needed_terms[key]['amount_currency'] += values['amount_currency']
                    else:
                        invoice.needed_terms[frozendict({
                            'move_id': invoice.id,
                            'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
                            'discount_date': False,
                            'discount_percentage': 0
                        })] = {
                            'balance': invoice.amount_total_signed,
                            'amount_currency': invoice.amount_total_in_currency_signed - 1 * invoice.total_disc_amount,
                            'name': invoice.payment_reference or '',
                        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    base_before_global_discounts = fields.Monetary(
        string="Amount Untaxed Before Discounts",
        readonly=True,
    )
    global_discount_item = fields.Boolean()
