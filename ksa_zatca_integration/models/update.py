from odoo import api, fields, models, exceptions
import logging

_zatca = logging.getLogger('Zatca Debugger for account.move :')


class ResCompanyUpdate(models.Model):
    _inherit = 'res.company'

    zatca_serial_number = fields.Char("Serial Number")
