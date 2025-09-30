# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseRequestFundingSource(http.Controller):
#     @http.route('/purchase_request_funding_source/purchase_request_funding_source', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_request_funding_source/purchase_request_funding_source/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_request_funding_source.listing', {
#             'root': '/purchase_request_funding_source/purchase_request_funding_source',
#             'objects': http.request.env['purchase_request_funding_source.purchase_request_funding_source'].search([]),
#         })

#     @http.route('/purchase_request_funding_source/purchase_request_funding_source/objects/<model("purchase_request_funding_source.purchase_request_funding_source"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_request_funding_source.object', {
#             'object': obj
#         })

