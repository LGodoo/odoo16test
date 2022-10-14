# -*- coding: utf-8 -*-
# from odoo import http


# class ServiceId(http.Controller):
#     @http.route('/service_id/service_id', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/service_id/service_id/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('service_id.listing', {
#             'root': '/service_id/service_id',
#             'objects': http.request.env['service_id.service_id'].search([]),
#         })

#     @http.route('/service_id/service_id/objects/<model("service_id.service_id"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('service_id.object', {
#             'object': obj
#         })
