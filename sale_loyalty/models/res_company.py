# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    loyalty_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', copy=True)
