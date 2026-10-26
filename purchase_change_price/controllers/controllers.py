# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseChangePrice(http.Controller):
#     @http.route('/purchase_change_price/purchase_change_price', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_change_price/purchase_change_price/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_change_price.listing', {
#             'root': '/purchase_change_price/purchase_change_price',
#             'objects': http.request.env['purchase_change_price.purchase_change_price'].search([]),
#         })

#     @http.route('/purchase_change_price/purchase_change_price/objects/<model("purchase_change_price.purchase_change_price"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_change_price.object', {
#             'object': obj
#         })
