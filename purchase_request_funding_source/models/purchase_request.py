# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def action_create_purchase_order(self):
        vendors = self.line_ids.mapped('suggested_vendor_id')
        if not vendors:
            raise UserError(
                _("No se puede crear una orden de compra. Por favor, sugiera al menos un proveedor en las líneas de productos."))

        group_by_funding_source = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_request_funding_source.po_group_by_funding_source')

        if group_by_funding_source:
            vendor_funding_groups = {}
            for line in self.line_ids:
                key = (line.suggested_vendor_id.id, line.funding_source_id.id)
                if key not in vendor_funding_groups:
                    vendor_funding_groups[key] = []
                vendor_funding_groups[key].append(line)

            for (vendor_id, funding_source_id), lines in vendor_funding_groups.items():
                po_vals = {
                    'partner_id': vendor_id,
                    'purchase_request_id': self.id,
                    'origin': self.name,
                    'date_order': fields.Datetime.now(),
                    'order_line': [
                        (0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.product_id.display_name,
                            'product_qty': line.quantity,
                            'price_unit': line.estimated_price,
                            'date_planned': self.date_needed,
                            'product_uom': line.product_id.uom_po_id.id,
                            'taxes_id': [(6, 0, line.taxes_id.ids)],
                        }) for line in lines
                    ]
                }
                self.env['purchase.order'].create(po_vals)
        else:
            return super(PurchaseRequest, self).action_create_purchase_order()

        self.write({'state': 'po_created'})
        return True


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    funding_source_id = fields.Many2one(
        comodel_name='purchase.request.funding.source',
        string='Fuente de Financiamiento',
        help='Fuente de financiamiento asociada a esta partida.',
    )
