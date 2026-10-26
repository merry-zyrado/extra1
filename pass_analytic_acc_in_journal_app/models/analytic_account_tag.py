# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    add_analytic_acc_tag = fields.Boolean(string="Analytic Account & Tags")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        result = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        # tags = [tag.id for tag in self.analytic_tag_ids]
        if self.analytic_account_id:
            for move_line in result:
                move_line.update({
                    'analytic_account_id': self.analytic_account_id.id,
                    # 'analytic_tag_ids':[(6,0,tags)]
                })   
        return result

    
    def action_post(self):
        result = super(AccountPayment, self).action_post()
        account_move = self.move_id
        # tags = [tag.id for tag in self.analytic_tag_ids]
        if self.analytic_account_id:
            for invoice_line in account_move.invoice_line_ids:
                invoice_line.update({
                    'analytic_account_id':self.analytic_account_id.id,
                    # 'analytic_tag_ids':[(6,0,tags)]
                })
        return result


class MyAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    add_analytic_acc_tag = fields.Boolean(string="Analytic Account & Tags")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")

    
    def _create_payment_vals_from_wizard(self):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_wizard()
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.analytic_account_id:
            result.update({
                # 'add_analytic_acc_tag': True,
                'analytic_account_id':self.analytic_account_id.id,
                # 'analytic_tag_ids':[(6,0,tags)]
            })
        return result

    def _create_payment_vals_from_batch(self):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_batch()
        # tags = [tag.id for tag in self.analytic_tag_ids]
        if self.analytic_account_id:
            result.update({
                'add_analytic_acc_tag': True,
                'analytic_account_id':self.analytic_account_id.id,
                # 'analytic_tag_ids':[(6,0,tags)]
            })
        return result


class accline(models.Model):
    _inherit = "account.move.line"

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
