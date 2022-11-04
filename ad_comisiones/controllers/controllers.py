# -*- coding: utf-8 -*-
# from odoo import http


# class MssComisiones(http.Controller):
#     @http.route('/ad_comisiones/ad_comisiones', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ad_comisiones/ad_comisiones/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ad_comisiones.listing', {
#             'root': '/ad_comisiones/ad_comisiones',
#             'objects': http.request.env['ad_comisiones.ad_comisiones'].search([]),
#         })

#     @http.route('/ad_comisiones/ad_comisiones/objects/<model("ad_comisiones.ad_comisiones"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ad_comisiones.object', {
#             'object': obj
#         })
