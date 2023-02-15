from pickle import TRUE
from odoo import api,fields,models,_
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class PurchaseMove(models.Model):
        _inherit = "purchase.move"
        liquidacion_id=fields.Many2one("pago_proveedores.liquidacion",string="Liquidacion")
        liquidacion_estado=fields.Selection(related='liquidacion_id.estado')
        liquidacion_move_state=fields.Selection(selection=[
            ('holding',_('En plazo')),
            ('due',_('A liquidar')),
            ('liquidated',_('Liquidada'))],
            string=_("Estado de Liquidación"),
            compute='_compute_liquidacion_move_state',
            store = True)
        
        @api.depends('liquidacion_id')
        def _compute_liquidacion_move_state(self):
            due = self.env['pago_proveedores.liquidacion'].get_due_date()
            print("_compute_liquidacion_move_state due=", due)
            for record in self:
                print("_compute_liquidacion_move_state", record,record.state,record.liquidacion_id,record.invoice_date)
                if record.liquidacion_id:
                    record.liquidacion_move_state = 'liquidated'
                elif record.state == 'posted' and record.invoice_date <= due:
                    record.liquidacion_move_state = 'due'
                else:
                    record.liquidacion_move_state = 'holding'
                
        @api.model
        def recompute_liquidacion_move_state(self):
            ''' Metodo llamado por ir_cron una vez por dia'''
            self.search([('state','=','posted')])._compute_liquidacion_move_state()
                
        def action_liquidate(self):
            # self es un recordset de uno o varios purchase.move
            # chequear que sean todos del mismo partner.
            #crear la liquidacion
            total_liquidacion=0
            if (all(x == self.partner_id[0] for x in self.partner_id) ):
                _logger.info("todos iguales")
            
            else:
                _logger.info("NO SON IGUALEs")
                
                raise ValidationError(_("Debe seleccionar facturas de unb solo Conductor"))
            
            for record in self:
                #agregar las purchase.move a la liquidacion
                _logger.info(self.liquidacion_id)
                _logger.info(len(record.liquidacion_id))

                if len(record.liquidacion_id)>0:
                    raise ValidationError(_("Una factura o mas se encuentran incluidas en otra liquidacion"))

            liquidacion = self.env['pago_proveedores.liquidacion'].create({'partner_id':self.partner_id.id})
           
            for record in self:
                #agregar las purchase.move a la liquidacion
                record.liquidacion_id = liquidacion.id
                total_liquidacion+=record.amount_total
            liquidacion.monto=total_liquidacion
            return {
                'name': 'Liquidación',
                'view_mode': 'form',
                'view_id': self.env.ref('pago_proveedores.liquidaciones_form').id,
                'res_model': 'pago_proveedores.liquidacion',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': liquidacion.id,
            }
            
        def action_remove_from_liquidacion(self):
            self.liquidacion_id = False
            
  
                

            
        
            

                
            
           
            
            
            
 

    