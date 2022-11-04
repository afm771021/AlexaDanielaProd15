# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.addons.sale.models.sale_order import SaleOrder
from odoo.exceptions import ValidationError
from odoo.fields import Datetime


class ad_comisiones(models.Model):
    _name = 'adcomisiones.adcomisiones'
    _description = 'Modelo para generacion de catalogo de comisiones'

    sale_criteria_type = fields.Selection([('I', 'Integrantes'), ('2', 'Monto Venta')], string='Criterio')
    sale_min = fields.Float(string='Mínimo')
    sale_max = fields.Float(string="Máximo")
    sale_commision_type = fields.Selection([('1', 'Monto'), ('2', 'Porcentaje')], string='Tipo Cálculo')
    sale_commision = fields.Float(string='Valor')
    sale_level = fields.Selection([('1', 'Nivel Lider'), ('2', 'Nivel Promotor')], string='Nivel')
    commision_status = fields.Boolean(string='Activo')

class AccountMoveCommissionGenerated(models.Model):
    _inherit = 'account.move'

    commission_generated = fields.Boolean(string='Comisión generada', default=False, readonly=True)

class CustomerAddInfo(models.Model):
    _inherit = 'res.partner'

    # Valor del crédito que tiene actualmente el venderor
    credit_amount = fields.Float(string='Crédito')
    # contacto que invito al vendedor actual
    guess_by = fields.Many2one(string='Invitador Por', comodel_name='res.partner')
    # RFC del vendedor
    #birthdate = fields.Date(string='Fecha nacimiento')
    birthday = fields.Selection([('1', '1'), ('2', '2'),('3', '3'), ('4', '4'),
                                 ('5', '5'), ('6', '6'),('7', '7'), ('8', '8'),
                                 ('9', '9'), ('10', '10'),('11', '11'), ('12', '12'),
                                 ('13', '13'), ('14', '14'),('15', '15'), ('16', '16'),
                                 ('17', '17'), ('18', '18'),('19', '19'), ('20', '20'),
                                 ('21', '21'), ('22', '22'),('23', '23'), ('24', '24'),
                                 ('25', '25'), ('26', '26'),('27', '27'), ('28', '28'),
                                 ('29', '29'), ('30', '30'),('31', '31')], string='Día Cumpleaños')

    birthmonth = fields.Selection([('Enero', 'Enero'), ('Febrero', 'Febrero'),('Marzo','Marzo'),
                                   ('Abril', 'Abril'), ('Mayo', 'Mayo'),('Junio','Junio'),
                                   ('Julio', 'Julio'), ('Agosto', 'Agosto'),('Septiembre','Septiembre'),
                                   ('Octubre', 'Octubre'), ('Noviembre', 'Noviembre'),('Diciembre','Diciembre')], string='Mes Cumpleaños')

    # Valor de comisiones ganadas
    commission_won = fields.Float(company_dependent=True)
    # ubicacion en mapa google maps
    website = fields.Char(string='Ubicación en Google', compute="_compute_google_map_location")
    @api.depends('partner_latitude','partner_longitude')
    def _compute_google_map_location(self):
        #self.ensure_one()
        self.website = 'https://www.google.com/maps/dir/?api=1&destination=' + str(self.partner_latitude) + ',' + str(self.partner_longitude)

    def action_partner_commission_history(self):
        self.ensure_one()
        if self.commission_won:
            return {
                'name': _('Pago de comisiones'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'adcommissions.commissionstopay',
                'domain': [('guess_by', 'in', self.ids), ('commision_status', "=", True)]
            }

class CustomSaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_paid = fields.Boolean(string='Comisión pagada', default=False, readonly=True)
    pending_amount = fields.Float(string='Saldo pendiente',compute="_pending_amount", readonly = True)


    @api.depends('partner_id')
    def _pending_amount(self):
        # se obtienen las facturas pendientes de pago y con pago parcial pendiente, se calcula y se muestra en pantalla
        sum_pending_payments = 0.0
        for record in self:
            pending_payments= self.env['account.move'].search([('partner_id', '=', record.partner_id.id),
                                            ('move_type', '=', 'out_invoice'),
                                            ('payment_state', 'in', ('not_paid','partial'))])
            for _pending_payment in pending_payments:
                sum_pending_payments = sum_pending_payments + _pending_payment.amount_residual

            record.pending_amount = sum_pending_payments

    # def button_interest(self):
    #     print(self.id)
    #     registros_a_eliminar = self.env['sale.order.line'].search([('product_id', '=', 2), ('order_id', '=', self.id)])
    #     for eliminar in registros_a_eliminar:
    #         eliminar.unlink()

class GenerateCommissionsPeriod(models.Model):
    _name = 'adcomisiones.adgeneracomisiones'
    _description = 'Modelo para generacion de comisiones'

    initDate = fields.Date(string='Fecha inicial', required=True)
    endDate = fields.Date(string='Fecha final', required=True)
    team_id = fields.Many2one('crm.team', string='Equipo', required=True)
    logdate = fields.Datetime(string='Fecha de generación', readonly=True)
    logcomments = fields.Text(string='Comentarios')
    commision_status = fields.Boolean(string="Generada", readonly=True)
    records = fields.Integer(string="No. Registros", readonly=True)
    promotors = 0
    leaders = 0

    def button_generar(self):
        #print('Generar Comisiones')
        self.commision_status = True
        sellers = []
        promotors = []
        leaders = []
        exist_promotor = False
        exist_seller = False
        exist_leader = False
        num_records = 0;

        # self.endDate = (datetime.strptime(self.endDate, '%Y-%m-%d')+relativedelta(days =+ 1))
        # self.endDate = self.endDate +timedelta(days=1)
        # Buscamos todas las ordenes con estatus de facturadas que no tengan comisione pagada y que sean de un equipo
        # de ventas en particular
        orders = self.env['sale.order'].search([('invoice_status', '=', 'invoiced'),
                                                ('commission_paid', '=', False),
                                                ('create_date','>=', self.initDate),
                                                ('create_date','<=', self.endDate),
                                                ('team_id', '=', self.team_id.id)])

        # Se recorren todas las ordenes para buscar los promotores y lideres
        for order in orders:
            #print(order, order.amount_total)
            #print('vendedor:', order.partner_id.id, order.partner_id.name)  # vendedor

            # si hay promotor
            if order.partner_id.guess_by.id:
                #print('promotor:', order.partner_id.guess_by.id, order.partner_id.guess_by.name)
                if len(promotors) > 0:
                    for i in range(len(promotors)):
                        # for j in range(len(promotors[i])):
                        # si el promotor ya existe en arreglo le sumamos un vendedor
                        if order.partner_id.guess_by.id == promotors[i][0]:
                            # bucamos que el vendedor no se repita
                            for j in range(len(sellers)):
                                #print(order.partner_id.id, sellers[j])
                                if order.partner_id.id == sellers[j]:
                                    exist_seller = True
                            # si el vencedor no existe, lo sumamos a la cuenta de vendedores del promotor
                            if not exist_seller:
                                promotors[i][1] = promotors[i][1] + 1
                                sellers.append(order.partner_id.id)
                            promotors[i][2] = promotors[i][2] + order.amount_total
                            exist_promotor = True
                            exist_seller = False

                    if not exist_promotor:
                        promotors.append([order.partner_id.guess_by.id, 1, order.amount_total,0.0])
                        sellers.append(order.partner_id.id)
                    exist_promotor = False
                else:
                    promotors.append([order.partner_id.guess_by.id, 1, order.amount_total,0.0])
                    sellers.append(order.partner_id.id)

             # si hay lider
            if order.partner_id.guess_by.guess_by.id:
                if len(leaders) > 0:
                    for i in range(len(leaders)):
                        # si el lider ya existe en arreglo
                        if order.partner_id.guess_by.guess_by.id == leaders[i][0]:
                            exist_leader = True
                            leaders[i][1] = leaders[i][1] + order.amount_total
                    if not exist_leader:
                        leaders.append([order.partner_id.guess_by.guess_by.id, order.amount_total,0.0])
                    exist_leader = False
                else:
                    leaders.append([order.partner_id.guess_by.guess_by.id, order.amount_total,0.0])
                # print(order.partner_id.guess_by.id)  # promotor
                # print(order.partner_id.guess_by.guess_by.id)  # lider
                # print(self.num_sellers_by_promotor(orders, order.partner_id.guess_by.id))

        # print('Promotores - ventas')
        # for i in range(len(promotors)):
        #     for j in range(len(promotors[i])):
        #         print(promotors[i][j], end=' ')
        #     print()
        #
        # print('Lider - ventas')
        # for i in range(len(leaders)):
        #     for j in range(len(leaders[i])):
        #         print(leaders[i][j], end=' ')
        #     print()

        _commission_values_N1 = self.env['adcomisiones.adcomisiones'].search(
            [('sale_level', '=', 1), ('commision_status', '=', True)])

        _commission_values_N2_amount = self.env['adcomisiones.adcomisiones'].search(
            [('sale_level', '=', 2), ('sale_criteria_type','=','2'), ('commision_status', '=', True)])

        _commission_values_N2_num_per = self.env['adcomisiones.adcomisiones'].search(
            [('sale_level', '=', 2), ('sale_criteria_type', '=', 'I'), ('commision_status', '=', True)])

        for i in range(len(promotors)):

            for commisionN2_num_per in _commission_values_N2_num_per:
                if promotors[i][1] >= commisionN2_num_per.sale_min and promotors[i][1] <= commisionN2_num_per.sale_max:
                    promotors[i][3] = commisionN2_num_per.sale_commision

            for commisionN2_ammount in _commission_values_N2_amount:
                if promotors[i][2] >= commisionN2_ammount.sale_min:
                    promotors[i][3] = commisionN2_ammount.sale_commision

        for i in range(len(leaders)):
            leaders[i][2] = _commission_values_N1.sale_commision

        print('Promotores - ventas')
        for i in range(len(promotors)):
            for j in range(len(promotors[i])):
                print(promotors[i][j], end=' ')
            print()

        print('Lider - ventas')
        for i in range(len(leaders)):
            for j in range(len(leaders[i])):
                print(leaders[i][j], end=' ')
            print()


        for order in orders:
            # print(order, order.id, order.amount_total)
            # print('vendedor:', order.partner_id.id, order.partner_id.name)
            # print('promotor:', order.partner_id.guess_by.id)
            # print('lider:', order.partner_id.guess_by.guess_by.id)

            invoice = self.env['account.move'].search([('invoice_origin', '=', order.name),
                                             ('move_type', '=', 'out_invoice'),
                                             ('state', '=', 'posted'),
                                             ('team_id', '=', order.team_id.id)])

            if invoice:
                invoice_details = self.env['account.move'].search([('ref', '=', invoice.payment_reference),
                                                 ('commission_generated', '=', False),
                                                 ('move_type', '=', 'entry'),
                                                 ('payment_id', '!=', False),
                                                 ('team_id', '=', order.team_id.id)])

                for invoice_detail in invoice_details:
                    if order.partner_id.guess_by.id:
                        for i in range(len(promotors)):
                            if order.partner_id.guess_by.id == promotors[i][0]:
                                _commissions_to_pay = {
                                    'sale_id': order.id,
                                    'guess_by': order.partner_id.guess_by.id,
                                    'seller_level': '2',
                                    'sale_amount': order.amount_total,
                                    'amortization_amount': invoice_detail.amount_total,
                                    'team_id': order.team_id.id,
                                    'commission': promotors[i][3],
                                    'commission_amount': (invoice_detail.amount_total * promotors[i][3]) / 100,
                                    'sale_date': order.date_order,
                                    'commission_paid': 0.0,
                                    'commision_status': False
                                }
                                self.env['adcommissions.commissionstopay'].create(_commissions_to_pay)
                                num_records += 1

                    if order.partner_id.guess_by.guess_by.id:
                        for i in range(len(leaders)):
                            if order.partner_id.guess_by.guess_by.id == leaders[i][0]:
                                _commissions_to_pay = {
                                    'sale_id': order.id,
                                    'guess_by': order.partner_id.guess_by.guess_by.id,
                                    'seller_level': '1',
                                    'sale_amount': order.amount_total,
                                    'amortization_amount': invoice_detail.amount_total,
                                    'team_id': order.team_id.id,
                                    'commission': leaders[i][2],
                                    'commission_amount': (invoice_detail.amount_total * leaders[i][2]) / 100,
                                    'sale_date': order.date_order,
                                    'commission_paid': 0.0,
                                    'commision_status': False
                                }
                                self.env['adcommissions.commissionstopay'].create(_commissions_to_pay)
                                num_records += 1
                    invoice_detail.commission_generated = True

            # promotor = self.env['adcommissions.commissionstopay'].search([('sale_id', '=', order.id),
            #                                                                  ('guess_by','=', order.partner_id.guess_by.id)])
            # if not promotor:
            #     if order.partner_id.guess_by.id:
            #         for i in range(len(promotors)):
            #             if order.partner_id.guess_by.id == promotors[i][0]:
            #                 _commissions_to_pay = {
            #                     'sale_id': order.id,
            #                     'guess_by': order.partner_id.guess_by.id,
            #                     'seller_level': '2',
            #                     'sale_amount': order.amount_total,
            #                     'team_id': order.team_id.id,
            #                     'commission': promotors[i][3],
            #                     'commission_amount': (order.amount_total * promotors[i][3]) /100,
            #                     'sale_date': order.date_order,
            #                     'commission_paid': 0.0,
            #                     'commision_status': False
            #                 }
            #                 self.env['adcommissions.commissionstopay'].create(_commissions_to_pay)
            #                 num_records += 1
            #
            # lider = self.env['adcommissions.commissionstopay'].search([('sale_id', '=', order.id),
            #                                                     ('guess_by', '=',order.partner_id.guess_by.guess_by.id)])
            # if not lider:
            #     if order.partner_id.guess_by.guess_by.id:
            #         for i in range(len(leaders)):
            #             if order.partner_id.guess_by.guess_by.id == leaders[i][0]:
            #                 _commissions_to_pay = {
            #                     'sale_id': order.id,
            #                     'guess_by': order.partner_id.guess_by.guess_by.id,
            #                     'seller_level': '1',
            #                     'sale_amount': order.amount_total,
            #                     'team_id': order.team_id.id,
            #                     'commission': leaders[i][2],
            #                     'commission_amount': (order.amount_total * leaders[i][2]) /100,
            #                     'sale_date': order.date_order,
            #                     'commission_paid': 0.0,
            #                     'commision_status': False
            #                 }
            #                 self.env['adcommissions.commissionstopay'].create(_commissions_to_pay)
            #                 num_records += 1

        self.records = num_records
        self.logdate = Datetime.now()

    @api.constrains('endDate')
    def _check_endDate(self):
        for record in self:
            if record.endDate < record.initDate:
                raise ValidationError("Fecha final debe ser mayor o igual a la fecha inicial")

class ad_commission_to_pay(models.Model):
     _name= 'adcommissions.commissionstopay'
     _description = 'Registro de las comisiones a pagar'

     sale_id = fields.Many2one(string='Nota de Venta', comodel_name='sale.order', required=True, readonly=True)
     guess_by = fields.Many2one(string='Nombre', comodel_name='res.partner')
     seller_level = fields.Selection([('1', 'Lider'), ('2', 'Promotor')], string='Nivel', readonly=True)
     sale_amount = fields.Float(string="Monto de la Nota", store=True, readonly=True)
     amortization_amount = fields.Float(string="Monto abonado", store=True, readonly=True)
     team_id = fields.Many2one('crm.team', string='Equipo', required=True)
     commission = fields.Float(string="% comisión", store=True, readonly=True)
     commission_amount = fields.Float(string="Monto de comisión", store=True, readonly=True)     # compute="_commission_amount", store=True)
     sale_date = fields.Datetime(string='Fecha venta', readonly=True)
     commission_pay_date = fields.Datetime(string='Fecha pago de comisión', readonly=True)
     commission_paid = fields.Float(string="Comision pagada", readonly=True)
     commision_status = fields.Boolean(string="Pagada", readonly=True)


     # _sql_constraints = [
     #     ('record_uniq', 'unique(sale_id, guess_by)', 'Ya existe el registro de pago de comisión!'),
     # ]

     def pay_commissions(self):
        #print ('boton header')
        order_paid = True
        for record in self:
            record.commision_status = True
            if record.commission_paid == 0.0:
                record.commission_pay_date = datetime.now()
                record.commission_paid = record.commission_amount
                record.guess_by.commission_won += record.commission_amount
        sellers = self.env['adcommissions.commissionstopay'].search([('sale_id', '=', record.sale_id.id)])

        # Se revisa que el lider y promotor tengan sus comisiones pagadas
        for seller in sellers:
            #print(seller)
            if not seller.commision_status:
                order_paid = False
        #print(order_paid)
        # Si ya tienen sus pagos se actualiza la orden a comision pagada
        if order_paid:
            #print(record.sale_id.id)
            order = self.env['sale.order'].search([('id', '=', record.sale_id.id)])
            order.write({
                 'commission_paid': True
            })
