from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_penalty_order = fields.Boolean(string='Penalty Order', compute="_compute_is_penalty_order", store=False)

    @api.depends('date_order')
    def _compute_is_penalty_order(self):
        d1 = self.date_order.date()
        d2 = datetime.today().date()
        days_difference = (d2 - d1).days
        print('date_order %s' % d1)
        print('today %s' % d2)
        print('days %d' % days_difference)

        penalty_rule = self.env['sale.penalty.rules'].search(
            [('start_days_late', '<=', days_difference), ('end_days_late', '>=', days_difference)])

        if penalty_rule:
            self.is_penalty_order = True
        else:
            self.is_penalty_order = False

    def action_penalty_order(self):
        print('action_penalty_order')
        OrderLineObj = self.env['sale.order.line']
        self.ensure_one()
        d1 = self.date_order.date()
        d2 = datetime.today().date()
        days_difference = (d2 - d1).days

        penalty_rule = self.env['sale.penalty.rules'].search(
            [('start_days_late', '<=', days_difference), ('end_days_late', '>=', days_difference)])

        if penalty_rule and len(penalty_rule) > 1:
            raise ValidationError(
                _("Revisar la configuración de Moras para las Ordenes de Venta, ya que existe más de un registro para %d días de atraso" % days_difference))

        if penalty_rule:
            penalty_prod = self.order_line.filtered(lambda x: x.product_id.id == penalty_rule.penalty_product_id.id)
            if penalty_prod:
                raise ValidationError(_("El registro de Moras ya existe en la Cotización"))
            OrderLineObj.create({
                'product_id': penalty_rule.penalty_product_id.id,
                'product_uom_qty': 1.0,
                'product_uom': penalty_rule.penalty_product_id.uom_id.id,
                'price_unit': penalty_rule.interest_rate * self.amount_total,
                #'reward_line': True,
                #'reward_type': 'gift',
                'order_id': self.id
            })
        return
