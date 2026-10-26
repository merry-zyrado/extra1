# -*- coding: utf-8 -*-
# from odoo import http


# class UpdateIccWork(http.Controller):
#     @http.route('/update_icc_work/update_icc_work', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/update_icc_work/update_icc_work/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('update_icc_work.listing', {
#             'root': '/update_icc_work/update_icc_work',
#             'objects': http.request.env['update_icc_work.update_icc_work'].search([]),
#         })

#     @http.route('/update_icc_work/update_icc_work/objects/<model("update_icc_work.update_icc_work"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('update_icc_work.object', {
#             'object': obj
#         })
