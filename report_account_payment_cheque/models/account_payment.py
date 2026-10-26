from num2words import num2words

from odoo import models, fields, api, _
import logging
from odoo import tools, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    amount_in_words = fields.Char(string="Amount in Words", compute="_compute_amount_to_text")

    @api.depends('amount')
    def _compute_amount_to_text(self):
        for record in self:
            def _num2words(number):
                try:
                    return num2words(number, lang='ar').replace(" و", " ").title()
                except NotImplementedError:
                    return num2words(number, lang='en').title()

            if num2words is None:
                record.amount_in_words = "The library 'num2words' is missing"
                return

            formatted = "%.2f" % record.amount
            parts = formatted.partition('.')
            integer_value = int(parts[0])
            fractional_value = int(parts[2] or 0)

            amount_words = f"{_num2words(integer_value)} ريال"
            if fractional_value > 0:
                amount_words += f" و {_num2words(fractional_value)} هللة"

            record.amount_in_words = amount_words
