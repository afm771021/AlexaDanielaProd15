from odoo import fields, models, api


class PenaltyRules(models.Model):
    _name = 'sale.penalty.rules'
    _description = 'Sale Penalty Rules'
    _check_company_auto = True

    name = fields.Text(string='Description', required=True)
    start_days_late = fields.Integer(string='Start Days Late', required=True)
    end_days_late = fields.Integer(string='End Days Late', required=True)
    interest_rate = fields.Float(string='Interest Rate', required=True, digits=(4, 2), default=0.0)
    penalty_product_id = fields.Many2one('product.product', string='Penalty Product', help='The product given as a Penalty')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)

