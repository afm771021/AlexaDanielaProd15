# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _name = 'sale.loyalty.program'
    _description = 'Sale Loyalty Program'

    name = fields.Char(string='Loyalty Program Name', index=True, required=True, help="An internal identification for the loyalty program configuration")
    pp_currency = fields.Float(string='Points per currency', digits='Sale Loyalty', help="How many loyalty points are given to the customer by sold currency")
    pp_product = fields.Float(string='Points per product', digits='Sale Loyalty', help="How many loyalty points are given to the customer by product sold")
    pp_order = fields.Float(string='Points per order', digits='Sale Loyalty', help="How many loyalty points are given to the customer for each sale or order")
    cumulative = fields.Boolean(string='Cumulative with rules')
    rounding = fields.Float(string='Points Rounding', required=True, default=1.000, digits='Sale Loyalty', help="The loyalty point amounts are rounded to multiples of this value.")
    rounding_method = fields.Selection([
        ('UP', 'UP'), ('DOWN', 'DOWN'), ('HALF-UP', 'HALF-UP')],
        string='Rounding Method', required=True,
        default='HALF-UP', help='The tie-breaking rule used for float rounding operations')
    rule_ids = fields.One2many('sale.loyalty.rule', 'loyalty_program_id', string='Rules')
    reward_ids = fields.One2many('sale.loyalty.reward', 'loyalty_program_id', string='Rewards')
    bonus_ids = fields.One2many('sale.loyalty.bonus', 'loyalty_program_id', string='Bonus')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    product_excluded_type = fields.Selection([
        ('type', 'Product Type'), ('categories', 'Categories'), ('products', 'Products')], string='Product Exclude Type')
    pe_product_type = fields.Selection([
        ('service', 'Service'), ('consu', 'Consumable'), ('product', 'Storable Product')], string='Based on Product Type')
    pe_categories = fields.Many2many('product.category', 'sale_loyalty_product_category_rel', 'category_id', 'sale_loyalty_id', string='Based on Product Categories')
    pe_products = fields.Many2many('product.product', 'sale_loyalty_product_rel', 'product_id', 'sale_loyalty_id', string='Based on Products')
    has_points_expiry = fields.Boolean('Can points expire?')
    points_expiry_days = fields.Integer('Expiry Days')

    @api.constrains('rounding')
    def validate_rounding(self):
        for record in self:
            if record.rounding <= 0:
                raise ValidationError(_("Please set a strictly positive rounding value."))


class LoyaltyRule(models.Model):
    _name = 'sale.loyalty.rule'
    _description = 'Sale Loyalty Rule'

    name = fields.Char(index=True, required=True, help="An internal identification for this loyalty program rule")
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this exception belongs to')
    rule_type = fields.Selection([('product', 'Product'), ('category', 'Category')], required=True, default='product', help='Does this rule affects products, or a category of products ?')
    product_id = fields.Many2one('product.product', string='Target Product', help='The product affected by the rule')
    category_id = fields.Many2one('product.category', string='Target Category', help='The category affected by the rule')
    cumulative = fields.Boolean(help='The points won from this rule will be won in addition to other rules')
    pp_product = fields.Float(string='Points Per Product', digits='Sale Loyalty', help='How many points the product will earn per product ordered')
    rounding = fields.Float(string='Points Rounding', required=True, default=1.000, digits='Sale Loyalty', help="The loyalty point amounts are rounded to multiples of this value.")
    rounding_method = fields.Selection([
        ('UP', 'UP'), ('DOWN', 'DOWN'), ('HALF-UP', 'HALF-UP')],
        string='Rounding Method', required=True,
        default='HALF-UP', help='The tie-breaking rule used for float rounding operations')
    pp_currency = fields.Float(string='Points Per Currency', digits='Sale Loyalty', help='How many points the product will earn per value sold')
    company_id = fields.Many2one(related='loyalty_program_id.company_id', string='Company', store=True, readonly=True, index=True)

    @api.constrains('rounding')
    def validate_rounding(self):
        for record in self:
            if record.rounding <= 0:
                raise ValidationError(_("Please set a strictly positive rounding value."))


class LoyaltyReward(models.Model):
    _name = 'sale.loyalty.reward'
    _description = 'Sale Loyalty Reward'

    name = fields.Char(index=True, required=True, help='An internal identification for this loyalty reward')
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    minimum_points = fields.Float(digits='Sale Loyalty', help='The minimum amount of points the customer must have to qualify for this reward')
    reward_type = fields.Selection([('gift', 'Gift'), ('discount', 'Discount')], required=True, help='The type of the reward')
    gift_product_id = fields.Many2one('product.product', string='Gift Product', help='The product given as a reward')
    point_cost = fields.Float(digits='Sale Loyalty', help='The cost of the reward')
    discount_product_id = fields.Many2one('product.product', string='Discount Product', help='The product used to apply discounts')
    discount = fields.Float(string="Discount(%)", help='The discount percentage')
    rounding = fields.Float(string='Points Rounding', required=True, default=1.000, digits='Sale Loyalty', help="The loyalty point amounts are rounded to multiples of this value.")
    rounding_method = fields.Selection([
        ('UP', 'UP'), ('DOWN', 'DOWN'), ('HALF-UP', 'HALF-UP')],
        string='Rounding Method', required=True,
        default='HALF-UP', help='The tie-breaking rule used for float rounding operations')
    company_id = fields.Many2one(related='loyalty_program_id.company_id', string='Company', store=True, readonly=True, index=True)

    @api.constrains('rounding')
    def validate_rounding(self):
        for record in self:
            if record.rounding <= 0:
                raise ValidationError(_("Please set a strictly positive rounding value."))

    @api.constrains('reward_type', 'gift_product_id')
    def _check_gift_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'gift' and not reward.gift_product_id):
            raise ValidationError(_('The gift product field is mandatory for gift rewards'))

    @api.constrains('reward_type', 'discount_product_id')
    def _check_discount_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'discount' and not reward.discount_product_id):
            raise ValidationError(_('The discount product field is mandatory for discount rewards'))

    @api.onchange('reward_type')
    def onchange_reward_type(self):
        if self.reward_type:
            if self.reward_type == 'discount':
                self.discount_product_id = self.env.ref('sale_loyalty.sale_loyalty_product_discount').id


class LoyaltyBonusRule(models.Model):
    _name = 'sale.loyalty.bonus'
    _description = 'Sale Loyalty Bonus'

    name = fields.Char(index=True, required=True, help="An internal identification for this loyalty program bonus")
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this exception belongs to')
    order_min_amount = fields.Float(string='Monto de venta mínimo')
    order_max_amount = fields.Float(string="Monto de venta máximo")
    pp_order = fields.Float(string='Points Per Order', digits='Sale Loyalty', help='How many points the order will earn per value sold')
    company_id = fields.Many2one(related='loyalty_program_id.company_id', string='Company', store=True, readonly=True, index=True)

    @api.constrains('order_min_amount')
    def validate_order_min_amount(self):
        for record in self:
            if record.order_min_amount <= 0:
                raise ValidationError(_("Please set a strictly positive value."))

    @api.constrains('order_max_amount')
    def validate_order_min_amount(self):
        for record in self:
            if record.order_max_amount <= 0:
                raise ValidationError(_("Please set a strictly positive value."))


class SaleLoyaltyPointsHistory(models.Model):
    _name = 'sale.loyalty.points.history'
    _description = 'Sale Loyalty Points History'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    date = fields.Datetime(required=True)
    expiry_date = fields.Date()
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    point_type = fields.Selection([('earn', 'Earned'), ('redeem', 'Redeemed')], string='Type', required=True, default='earn')
    points = fields.Float(required=True, digits='Sale Loyalty')
    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'),
        ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='draft', required=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            return {'domain': {'sale_order_id': [('partner_id', '=', self.partner_id.id)]}}

    def action_cancel(self):
        for history in self:
            history.write({'state': 'cancelled'})

    def action_draft(self):
        for history in self:
            history.write({'state': 'draft'})

    @api.model
    def _cron_expire_points(self):
        phs = self.search([('expiry_date', '<=', fields.Date.context_today(self)), ('point_type', '=', 'earn'), ('state', '=', 'confirmed')])
        for ph in phs:
            ph.write({'state': 'expired'})
            ph.partner_id.loyalty_points -= ph.points
