# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    points_won = fields.Float(string="Bonos generado", compute='compute_points_won', digits='Sale Loyalty')
    points_spent = fields.Float(string="Bonos gastado", compute='compute_points_spent', digits='Sale Loyalty')
    points_total = fields.Float(string="Total Bonos", compute='compute_points_total', digits='Sale Loyalty')
    temp_points_won = fields.Float(digits='Sale Loyalty')
    temp_points_spent = fields.Float(digits='Sale Loyalty')
    temp_points_total = fields.Float(digits='Sale Loyalty')
    reward_line_available = fields.Boolean(compute='compute_reward_line_available')
    cancel_points = fields.Boolean(string="Cancelar Bonos", default=False)

    @api.depends('order_line.reward_line')
    def compute_reward_line_available(self):
        for order in self:
            order.reward_line_available = False
            if any(o.reward_line for o in order.order_line):
                order.reward_line_available = True

    @api.depends('partner_id.loyalty_points', 'points_won', 'points_spent')
    def compute_points_total(self):
        for order in self:
            order.points_total = 0.00
            if order.points_won or order.points_spent:
                order.points_total = order.points_won + order.points_spent
            # si se cancela el bono
            if order.cancel_points:
                order.points_won = 0.00
                if order.points_won or order.points_spent:
                    order.points_total = order.points_won + order.points_spent
        #print('compute_points_total')

    @api.depends('order_line.total_spent_point')
    def compute_points_spent(self):
        for order in self:
            order.points_spent = 0.00
            if order.order_line:
                order.points_spent = sum(order.order_line.mapped('total_spent_point')) * -1

    @api.depends('order_line')
    def compute_points_won(self):
        #print ('compute_points_won')
        for order in self:
            loyalty = order.company_id.loyalty_id
            order.points_won = 0.00
            if loyalty:
                points = 0.00
                order_lines = order.order_line
                if loyalty.product_excluded_type == 'type':
                    if loyalty.pe_product_type == 'service':
                        order_lines = order_lines.filtered(lambda x: x.product_id.type != 'service')
                    elif loyalty.pe_product_type == 'consu':
                        order_lines = order_lines.filtered(lambda x: x.product_id.type != 'consu')
                    elif loyalty.pe_product_type == 'product':
                        order_lines = order_lines.filtered(lambda x: x.product_id.type != 'product')
                elif loyalty.product_excluded_type == 'categories' and loyalty.pe_categories:
                    order_lines = order_lines.filtered(lambda x: x.product_id.categ_id not in loyalty.pe_categories)
                elif loyalty.product_excluded_type == 'products' and loyalty.pe_products:
                    order_lines = order_lines.filtered(lambda x: x.product_id not in loyalty.pe_products)
                if order_lines:
                    points += float_round(loyalty.pp_order, precision_rounding=loyalty.rounding, rounding_method=loyalty.rounding_method)
                if ((loyalty.rule_ids or loyalty.bonus_ids) and loyalty.cumulative) or (not loyalty.rule_ids and not loyalty.bonus_ids):
                    if loyalty.pp_currency:
                        points += float_round(sum(order_lines.mapped('price_total')) * loyalty.pp_currency, precision_rounding=loyalty.rounding, rounding_method=loyalty.rounding_method)
                    if loyalty.pp_product:
                        total_point = sum(order_lines.mapped('product_uom_qty')) * loyalty.pp_product
                        points += float_round(total_point, precision_rounding=loyalty.rounding, rounding_method=loyalty.rounding_method)
                if loyalty.rule_ids and ((loyalty.bonus_ids and loyalty.cumulative) or (not loyalty.bonus_ids)):
                    for rule in loyalty.rule_ids:
                        if rule.rule_type == 'product':
                            lines = order_lines.filtered(lambda l: l.product_id == rule.product_id)
                        else:
                            lines = order_lines.filtered(lambda l: l.product_id.categ_id == rule.category_id)
                        if lines:
                            if rule.pp_product and not rule.cumulative:
                                total_qty = sum(lines.mapped('product_uom_qty'))
                                points += float_round((total_qty * rule.pp_product), precision_rounding=rule.rounding, rounding_method=rule.rounding_method)
                            if rule.pp_currency and not rule.cumulative:
                                total_price = sum(lines.filtered(lambda l: not l.reward_line).mapped('price_subtotal'))
                                points += float_round((total_price * rule.pp_currency), precision_rounding=rule.rounding, rounding_method=rule.rounding_method)
                            if rule.cumulative:
                                total_price = sum(lines.mapped('price_subtotal'))
                                pp_product_point = sum(lines.mapped('product_uom_qty')) * rule.pp_product
                                if rule.pp_currency:
                                    pp_currency_point = total_price * rule.pp_currency
                                else:
                                    pp_currency_point = total_price * loyalty.pp_currency
                                points += float_round((pp_currency_point + pp_product_point), precision_rounding=rule.rounding, rounding_method=rule.rounding_method)
                if loyalty.bonus_ids:
                    order_amount = sum(order_lines.mapped('price_total'))
                    bonus = loyalty.bonus_ids.filtered(lambda x: x.order_min_amount <= order_amount and x.order_max_amount >= order_amount)
                    if bonus and len(bonus) == 1:
                        points += bonus.pp_order;
                order.points_won = points
        if order.cancel_points:
            order.points_won = 0.00

    def action_confirm(self):
        for order in self:
            if order.partner_id:
                loyalty = order.company_id.loyalty_id
                PointsHistory = self.env['sale.loyalty.points.history']
                if order.points_won:
                    earn_history_obj = PointsHistory.search([('sale_order_id', '=', order.id), ('point_type', '=', 'earn')])
                    if not earn_history_obj:
                        self.env['sale.loyalty.points.history'].sudo().create({
                            'partner_id': order.partner_id.id,
                            'sale_order_id': order.id,
                            'date': fields.Datetime.now(),
                            'expiry_date': fields.Date.context_today(self) + relativedelta(days=loyalty.points_expiry_days) if loyalty.has_points_expiry and loyalty.points_expiry_days > 0 else False,
                            'point_type': 'earn',
                            'points': order.points_won,
                            'state': 'confirmed'
                        })
                        order.partner_id.loyalty_points += order.points_won
                    else:
                        earn_history_obj.sudo().write({
                            'partner_id': order.partner_id.id,
                            'date': fields.Datetime.now(),
                            'points': order.points_won,
                            'state': 'confirmed'
                        })
                if order.points_spent:
                    redeem_history_obj = PointsHistory.search([('sale_order_id', '=', order.id), ('point_type', '=', 'redeem')])
                    if not redeem_history_obj:
                        self.env['sale.loyalty.points.history'].sudo().create({
                            'partner_id': order.partner_id.id,
                            'sale_order_id': order.id,
                            'date': fields.Datetime.now(),
                            'expiry_date': fields.Date.context_today(self) + relativedelta(days=loyalty.points_expiry_days) if loyalty.has_points_expiry and loyalty.points_expiry_days > 0 else False,
                            'point_type': 'redeem',
                            'points': order.points_spent,
                            'state': 'confirmed'
                        })
                        order.partner_id.loyalty_points += order.points_spent
                    else:
                        redeem_history_obj.sudo().write({
                            'partner_id': order.partner_id.id,
                            'date': fields.Datetime.now(),
                            'points': order.points_won,
                            'state': 'confirmed'
                        })

                order.temp_points_won = order.points_won
                order.temp_points_spent = order.points_spent
                order.temp_points_total = order.points_won + order.points_spent
        return super(SaleOrder, self).action_confirm()

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            points_history = self.env['sale.loyalty.points.history'].search([('sale_order_id', '=', order.id)])
            if points_history:
                order.partner_id.loyalty_points -= order.points_won
                points_history.action_cancel()
        return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        for order in self:
            points_history = self.env['sale.loyalty.points.history'].search([('sale_order_id', '=', order.id)])
            if points_history:
                points_history.action_draft()
        return res

    def unlink(self):
        for order in self:
            points_history = self.env['sale.loyalty.points.history'].search([('sale_order_id', '=', order.id)])
            if points_history:
                points_history.unlink()
        return super(SaleOrder, self).unlink()

    def action_apply_bonus(self):
        #print('aplicar Bono')
        for order in self:
            order.cancel_points = False

    def action_cancel_bonus(self):
        #print('Cancelar Bono')
        for order in self:
            order.cancel_points = True

    def action_redeem_points(self):
        self.ensure_one()
        if self.amount_total <= 0.00:
            raise UserError(_('El vendedor no puede usar Bonos en una nota con valor 0 !!')) #Customer can not redeem points on 0 amount order !'))
        if self.partner_id.loyalty_points <= 0.00:
            raise UserError(_("El vendedor no tiene monto de Bono a utilizar ! ")) #Customer don't have any loyalty points to redeem !"))
        loyalty = self.company_id.loyalty_id
        if not loyalty:
            raise UserError(_('No existe la configuración para el programa de Bonos ! ')) #There is no loyalty program set in sale configuration !'))

        pd = self.env['decimal.precision'].precision_get('Sale Loyalty')
        product = self.env.ref('sale_loyalty.sale_loyalty_product_redeem')
        default_points = min(self.partner_id.loyalty_points + self.points_spent, float_round(self.amount_total / product.lst_price, precision_digits=pd) + self.points_spent)

        if default_points <= 0.00:
            raise UserError(_("El vendedor no tiene suficiente monto de bono para utilizar ! ")) #Customer don't have enough loyalty points to redeem !"))
        ctx = self.env.context.copy()
        ctx.update({'default_order_id': self.id, 'default_loyalty_id': loyalty.id, 'default_points': default_points})
        return {
            'name': "How much points do you want to redeem ?",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'point.selection.wizard',
            'context': ctx,
            'target': 'new',
        }

    def button_reward(self):
        OrderLineObj = self.env['sale.order.line']
        loyalty = self.company_id.loyalty_id
        if not loyalty:
            raise UserError(_('There is no loyalty program set in sale configuration !'))
        if not loyalty.reward_ids:
            raise UserError(_('There is no reward available for the current loyalty program !'))
        for reward in sorted(loyalty.reward_ids, key=lambda l: l.reward_type):
            if (self.points_total + self.partner_id.loyalty_points - self.points_won) >= reward.minimum_points:
                if reward.reward_type == 'gift':
                    OrderLineObj.create({
                        'product_id': reward.gift_product_id.id,
                        'product_uom_qty': 1.0,
                        'product_uom': reward.gift_product_id.uom_id.id,
                        'price_unit': 0.0,
                        'spent_point': float_round(reward.point_cost, precision_rounding=reward.rounding, rounding_method=reward.rounding_method),
                        'reward_line': True,
                        'reward_type': 'gift',
                        'order_id': self.id
                    })
                    self.compute_points_spent()
                elif reward.reward_type == 'discount':
                    discount = (self.amount_untaxed * (reward.discount / 100)) * -1
                    discount_point_cost = (discount * reward.point_cost) * -1
                    if discount_point_cost >= self.partner_id.loyalty_points:
                        discount = (self.partner_id.loyalty_points / reward.point_cost) * -1
                        discount_point_cost = (discount * reward.point_cost) * -1
                    OrderLineObj.create({
                        'product_id': reward.discount_product_id.id,
                        'product_uom_qty': 1.0,
                        'product_uom': reward.discount_product_id.uom_id.id,
                        'price_unit': discount,
                        'spent_point': float_round(discount_point_cost, precision_rounding=reward.rounding, rounding_method=reward.rounding_method),
                        'reward_line': True,
                        'reward_type': 'discount',
                        'order_id': self.id
                    })
                    self.compute_points_spent()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    reward_line = fields.Boolean(string='Reward Line ?')
    spent_point = fields.Float(string='Spent Points', digits='Sale Loyalty')
    total_spent_point = fields.Float(compute='compute_total_spent_point', string='Total Spent Points', digits='Sale Loyalty')
    reward_type = fields.Selection((('gift', 'Gift'), ('discount', 'Discount'), ('resale', 'Resale')))

    @api.depends('spent_point', 'product_uom_qty')
    def compute_total_spent_point(self):
        for line in self:
            line.total_spent_point = 0.00
            if line.reward_type == 'gift':
                line.total_spent_point = line.spent_point * line.product_uom_qty
            if line.reward_type == 'discount' and line.product_uom_qty == 1:
                line.total_spent_point = line.spent_point
            if line.reward_type == 'resale':
                line.total_spent_point = line.spent_point
