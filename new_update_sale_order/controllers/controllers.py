# -*- coding: utf-8 -*-
# from odoo import http


# class NewUpdateSaleOrder(http.Controller):
#     @http.route('/new_update_sale_order/new_update_sale_order', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/new_update_sale_order/new_update_sale_order/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('new_update_sale_order.listing', {
#             'root': '/new_update_sale_order/new_update_sale_order',
#             'objects': http.request.env['new_update_sale_order.new_update_sale_order'].search([]),
#         })

#     @http.route('/new_update_sale_order/new_update_sale_order/objects/<model("new_update_sale_order.new_update_sale_order"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('new_update_sale_order.object', {
#             'object': obj
#         })
