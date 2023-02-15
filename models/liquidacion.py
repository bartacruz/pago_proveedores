from odoo import _,models,fields,api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class liquidacion(models.Model):
    _name = 'pago_proveedores.liquidacion'
    
    # Los documentos en Odoo tienen una compania y una moneda asignada, que facilita el procesamiento de montos.
    # Definidos asi, se calculan automaticamente desde el usuario que los crea
    
    name = fields.Char(
        string="Name",
        required=True,
        index=True,
        copy=False,
        default='/',
    )
    company_id = fields.Many2one(
        "res.company",
        string=_("Company"),
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id
    )
    
    purchase_move_ids= fields.One2many("purchase.move","liquidacion_id",string=_("Facturas"))
    currency_id = fields.Many2one(related='company_id.currency_id', depends=["company_id"], store=True, ondelete="restrict")
    
    monto = fields.Monetary(string="Monto total")
    monto2= fields.Monetary(string="Total Liquidado",compute="_compute_amount")
    pago_ids =fields.One2many(
        "pago_proveedores.pagos",
        "liquidacion_id",
        string=_("Pagos"),
        index=True,
        ondelete="restrict"
    )
    fecha = fields.Date(string="Fecha Liquidacion", default=fields.Datetime.now)
    
    partner_id = fields.Many2one(
        "res.partner",
        string=_("Partner"),
        required=True,
        index=True,
        ondelete="restrict"
    )
    
    estado = fields.Selection([("B", "Borrador"),("E", "Enviado"),("C", "Controlado"),("A", "Aprobado"),("P", "Pagado")],string="Estado",index=True, default="B")
    observaciones = fields.Text(string="Observaciones")

    document_number = fields.Integer(_('Document Number'), compute='_compute_document_number', store=True)
   
    @api.onchange('purchase_move_ids')
    def check_liquidacion_id(self):
        facturas=self.env['purchase.move']
        _logger.info(self.purchase_move_ids)
        for record in facturas:
            _logger.info(record.liquidacion_id)
            if record.liquidacion_id!=False:
                raise ValidationError("la factura ya fue incluida en otra liquidacion")


    def action_enviado(self):
        for record in self:
          record.estado='E'

    def action_controlado(self):
          self.ensure_one()
          self.estado=('C')

    def action_aprobado(self):
          self.ensure_one()
          self.estado=('A')
          self._check_name()

    def action_pagado(self):
          self.ensure_one()
          self.estado=('P')
    
    
    @api.depends('purchase_move_ids','monto2')
    def _compute_amount(self):
        for record in self:
            record.monto2 = sum(record.purchase_move_ids.mapped('amount_total'))
    
    @api.depends('partner_id')
    def _compute_document_number(self):
        if self.document_number or not self.partner_id:
            return
        numbers = self.env[self._name].search([('partner_id','=',self.partner_id.id)] ).mapped('document_number')
        
        if numbers:
            numbers.sort()
            self.document_number = numbers[-1] +1
        else:
            self.document_number = 1

    def _check_name(self):
        if self.name == '/' and self.document_number :
            self.name = '%s-%06d' % ('Liquidacion',self.document_number)
        
