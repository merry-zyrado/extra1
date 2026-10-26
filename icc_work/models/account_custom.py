from odoo import api, fields, models

class AddProjectName(models.Model):
    _inherit = 'account.move'
    project_id = fields.Many2one('project.project',string='Project Name')
    account_custom_id = fields.Many2one('sale.order','Sale order Id',)
    _order = "id asc"









