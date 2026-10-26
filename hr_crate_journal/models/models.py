from odoo import api, fields, models

class HrCreateJournal(models.Model):
    _inherit = 'hr.payslip.run'

    credit_id = fields.Many2one('account.account', string="Credit account")
    debit_id = fields.Many2one('account.account', string="Debit account")
    account_id = fields.Many2one('account.move', string="Journal Id")
    total_amount = fields.Float(string="Total")
    journal_id = fields.Many2one('account.journal'
       )




    def get_hr_payslip(self):

        all_pay = 0

        payslib = self.env['hr.payslip'].search([('payslip_run_id', '=', self.id)
        ])
        print(payslib,'pay')

        for rec in payslib:
            all_pay += rec.net_wage

        print(all_pay,'all')

        self.total_amount = all_pay

        lines = []
        for rec in self:
            lines.append((0, 0, {
                    'account_id': rec.debit_id.id,
                    'debit': rec.total_amount,

                }))

            print(lines)
            lines.append((0, 0, {
                                'account_id': rec.credit_id.id,
                                'credit': rec.total_amount,

                            }))

            print(lines)

            lines_statments = {

                'ref': self.name,
                'journal_id': self.journal_id.id,
                'line_ids': lines
            }

        invoice_id = self.env['account.move'].create(lines_statments)
        self.account_id = invoice_id.id











