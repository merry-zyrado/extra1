# -*- coding: utf-8 -*-
# from odoo import http


# class UpdateProject(http.Controller):
#     @http.route('/update_project/update_project', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/update_project/update_project/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('update_project.listing', {
#             'root': '/update_project/update_project',
#             'objects': http.request.env['update_project.update_project'].search([]),
#         })

#     @http.route('/update_project/update_project/objects/<model("update_project.update_project"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('update_project.object', {
#             'object': obj
#         })
