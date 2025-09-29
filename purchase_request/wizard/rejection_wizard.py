from odoo import models, fields, api

class PurchaseRequestRejectionWizard(models.TransientModel):
    _name = 'purchase.request.rejection.wizard'
    _description = 'Asistente para Motivo de Rechazo de Solicitud de Compra'

    rejection_reason = fields.Text(string='Motivo del Rechazo', required=True)

    def action_confirm_rejection(self):
        purchase_request = self.env['purchase.request'].browse(self._context.get('active_id'))
        purchase_request.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason
        })
        return {'type': 'ir.actions.act_window_close'}