from odoo import api, fields, models 

class ReceiptReport(models.Model):
    _name = 'receipt.report'
    _description = 'ReceiptReport'

    name = fields.Char('Receipt Report Description')
    code = fields.Char('Item Code')
    date_recipt = fields.Date(string="Receipt Report Date")
    is_active = fields.Boolean('Active')
    account = fields.Integer('QTY')
    sale_id = fields.Many2one(comodel_name="sale.order")


    
