from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ProjectReport(models.TransientModel):
    _name = "project.report"

    partner_id = fields.Many2one('res.partner', string="Client", required=True,)
    date_from = fields.Date(string="From Date", required=True,default=fields.Date.today )
    date_to = fields.Date(string="To Date", required=True)
    project_ids = fields.Many2many('project.project', string='Project Name ',)




    def action_print_product_moves_pdf_1(self) :
        return self.env.ref('icc_work.action_product_onhand_report_4').report_action(self)

    def get_action_print_product_onhand_summary_pdf(self) :
        print(datetime.today(),'dddddddddd')
        lst = []
        in_bal_total = []

        code = 1
        for project in self.project_ids:
            projects = self.env['sale.order'].search([
                ('date_order_custom', '>=', self.date_from),
                ('date_order_custom', '<=', self.date_to),
                ('partner_id', '=', self.partner_id.id),
                ('project_id', '=', project.id),
                ('state', '=', 'sale'),
            ])
            print(projects,'projects')
            if projects.account_id:
                print( projects.account_id,' projects.account_id')
                for pro in projects:
                    print(pro.amount_due,'account_id')
                    credit = 0
                    for line in pro.account_id:

                        print(line)
                        if line:
                            credit += line.amount_total
                            lst.append(
                                    {
                                        'code' : code,
                                        'project_name' : pro.project_id.name,
                                        'project_total' : pro.amount_total,
                                        'payment_date' : line.invoice_date or '',
                                        'debit' : line.amount_total or '',
                                        'credit' : pro.amount_total - credit,
                                        'balance' :  pro.amount_total - credit,


                                    })
                            print(lst)
            if not projects.account_id:
                print(projects, 'projects')
                print('False')
                print(projects.project_id.id, 'pro.project_id.name')

                lst.append(
                    {
                        'code' : code,
                        'project_name' : projects.project_id.name,
                        'project_total' : projects.amount_total,
                        'payment_date' : '',
                        'debit' : '',
                        'credit' : projects.amount_total ,
                        'balance' : projects.amount_total ,

                    })
                print(lst)
        return lst














