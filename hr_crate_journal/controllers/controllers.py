# -*- coding: utf-8 -*-
# from odoo import http


# class HrCrateJournal(http.Controller):
#     @http.route('/hr_crate_journal/hr_crate_journal', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_crate_journal/hr_crate_journal/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_crate_journal.listing', {
#             'root': '/hr_crate_journal/hr_crate_journal',
#             'objects': http.request.env['hr_crate_journal.hr_crate_journal'].search([]),
#         })

#     @http.route('/hr_crate_journal/hr_crate_journal/objects/<model("hr_crate_journal.hr_crate_journal"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_crate_journal.object', {
#             'object': obj
#         })
