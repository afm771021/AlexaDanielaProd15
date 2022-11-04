from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    return_line = fields.One2many('sale.order.return', 'order_id', string='Order Return Lines',
                                  states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                  auto_join=True)
    pending_return_lines = fields.Boolean(string='Pending Return Lines', compute="_compute_pending_return_lines", store=False)

    @api.depends('return_line')
    def _compute_pending_return_lines(self):
        self.ensure_one()
        for order in self:
            return_lines = order.return_line.filtered(lambda x: x.processed is False)
            if return_lines:
                self.pending_return_lines = True
            else:
                self.pending_return_lines = False

    def action_return_products(self):
        print('action_return_products')
        self.ensure_one()
        for order in self:
            return_lines = order.return_line.filtered(lambda x: x.processed is False)
            if return_lines:
                for line_ret in return_lines:
                    processed = False
                    order_line = order.order_line.filtered(lambda x: x.product_id.id == line_ret.product_id.id)
                    if order_line:
                        for line in order_line:
                            if line.product_uom_qty - 1 >= 0:
                                line.product_uom_qty = line.product_uom_qty - 1
                                processed = True
                                break
                            # elif line.product_uom_qty - 1 == 0:
                            #     line.unlink()
                            #     processed = True
                            #     break
                        line_ret.processed = processed
        return

    def action_confirm(self):
        print('action_confirm... return products')
        for order in self:
            return_lines = order.return_line.filtered(lambda x: x.processed is False)
            if return_lines:
                raise ValidationError(_("No es posible confirmar la Cotización con productos devueltos, pendientes de procesar!"))
        return super(SaleOrder, self).action_confirm()
