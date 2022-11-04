from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang


class SaleOrderReturnLine(models.Model):
    _name = 'sale.order.return'
    _description = 'Sales Order Return Line'
    _order = 'order_id, id'
    _check_company_auto = True

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    processed = fields.Boolean(string='Processed', default=False)

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson')
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True,
                                  string='Currency')
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', index=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return

        lang = get_lang(self.env, self.order_id.partner_id.lang).code
        product = self.product_id.with_context(
            lang=lang,
        )

        self.update({'name': product.display_name})

    @api.constrains('product_id')
    def _check_product(self):
        for record in self:
            rec = self.env['sale.order.line'].search([('order_id', '=', record.order_id.id), ('product_id', '=', record.product_id.id)])
            if not rec:
                raise ValidationError(_("El producto (%s) debe existir en la Cotización") % record.name)
