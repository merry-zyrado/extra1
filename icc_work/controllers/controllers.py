# -*- coding: utf-8 -*-
# from odoo import http


# class IccWork(http.Controller):
#     @http.route('/icc_work/icc_work', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/icc_work/icc_work/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('icc_work.listing', {
#             'root': '/icc_work/icc_work',
#             'objects': http.request.env['icc_work.icc_work'].search([]),
#         })

#     @http.route('/icc_work/icc_work/objects/<model("icc_work.icc_work"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('icc_work.object', {
#             'object': obj
#         })
