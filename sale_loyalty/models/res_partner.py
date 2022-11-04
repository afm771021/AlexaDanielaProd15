# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

from odoo import models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Float(company_dependent=True, help='The loyalty points the user won as part of a Loyalty Program')
    sale_loyalty_points_history = fields.One2many('sale.loyalty.points.history', 'partner_id', string='Loyalty History')

    def get_loyalty_points_history(self):
        self.ensure_one()
        points_history = self.env['sale.loyalty.points.history'].search([('partner_id', '=', self.id), ('state', '=', 'confirmed')])
        return points_history

    def get_commission_history(self):
        self.ensure_one()
        commission_history = self.env['adcommissions.commissionstopay'].search([('guess_by','=',self.id),('commision_status','=',True)])
        return commission_history

    def get_portal_pdf_url(self, suffix=None, report_type=None, download=None):
        self.ensure_one()
        url = '/my/loyalty/history/%s?%s%s' % (
            self.id,
            'report_type=%s' % report_type if report_type else '',
            '&download=true' if download else ''
        )
        return url

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s - Loyalty Points Report' % (self.name)

    def action_partner_loyalty_points_history(self):
        self.ensure_one()
        if self.sale_loyalty_points_history:
            return {
                'name': _('Partner Loyalty Points History'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'sale.loyalty.points.history',
                'domain': [('id', 'in', self.sale_loyalty_points_history.ids)]
            }
