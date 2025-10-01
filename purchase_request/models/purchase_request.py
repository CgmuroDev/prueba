# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Solicitud de Compra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc,date_needed desc ,id desc'

    name = fields.Char(
        string='Folio', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'))

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        index=True,
        default=lambda self: self.env.company,
        tracking=True,
    )

    requester_id = fields.Many2one(
        'res.users', string='Solicitante', required=True,
        default=lambda self: self.env.user, tracking=True)

    department_id = fields.Many2one('hr.department', string='Departamento',
                                    related='requester_id.employee_id.department_id', store=True, tracking=True)

    date_needed = fields.Date(string='Fecha Requerida', required=True, tracking=True)

    justification = fields.Text(string='Justificación', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'No Prioridad'),
        ('1', 'Normal'),
        ('2', 'Urgente'),
        ('3', 'Muy Urgente')
    ], string='Prioridad', default='0')

    line_ids = fields.One2many(
        'purchase.request.line', 'request_id',
        string='Líneas de Solicitud', required=True)



    purchase_order_ids = fields.One2many('purchase.order', 'purchase_request_id', string='Órdenes de Compra')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count', string='# de Órdenes')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('to_approve', 'Pendiente de Aprobar'),
        ('approved', 'Aprobado'),
        ('po_created', 'Órdenes Creadas'),
        ('rejected', 'Rechazado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    rejection_reason = fields.Text(string='Motivo del Rechazo', readonly=True, tracking=True)

    total_amount = fields.Float(string='Monto Total', compute='_compute_total_amount', store=True)

    kanban_state_color = fields.Integer(string='Color de Estado Kanban', compute='_compute_kanban_state_color')


    @api.model
    def create(self, vals):
        request = super(PurchaseRequest, self).create(vals)
        if request.requester_id:
            request.message_subscribe(partner_ids=[request.requester_id.partner_id.id])
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super(PurchaseRequest, self).create(vals)


    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = len(request.purchase_order_ids)

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for request in self:
            request.total_amount = sum(request.line_ids.mapped('subtotal'))


    @api.depends('state')
    def _compute_kanban_state_color(self):
        for request in self:
            color = 1
            if request.state == 'draft':
                color = 4
            elif request.state == 'to_approve':
                color = 2
            elif request.state in ['approved', 'po_created']:
                color = 10
            elif request.state in ['rejected', 'cancel']:
                color = 1
            request.kanban_state_color = color

    def action_submit_for_approval(self):
        self.write({'state': 'to_approve'})
        try:
            approver_group = self.env.ref('purchase_request.group_purchase_request_manager')
            self.message_subscribe(partner_ids=approver_group.users.partner_id.ids)
        except ValueError:
            raise UserError(_("No se ha encontrado el grupo de aprobadores de solicitud de compra."))


        for user in approver_group.users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Aprobar Solicitud de Compra'),
                note=_('Una nueva solicitud de compra (%s) requiere su aprobación.') % self.name,
                user_id=user.id
            )

        self.message_post(body=_('Solicitud enviada para aprobación. Pendiente de los aprobadores.'))

    def action_approve(self):
        self.write({'state': 'approved'})
        self.message_post(body="Tu solicitud de compra ha sido aprobada.")
        template = self.env.ref('purchase_request.email_template_purchase_request_approved', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_create_purchase_order(self):
        vendors = self.line_ids.mapped('suggested_vendor_id')
        if not vendors:
            raise UserError(
                _("No se puede crear una orden de compra. Por favor, sugiera al menos un proveedor en las líneas de productos."))

        for vendor in vendors:
            vendor_lines = self.line_ids.filtered(lambda line: line.suggested_vendor_id == vendor)

            po_vals = {
                'partner_id': vendor.id,
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
                    }) for line in vendor_lines
                ]
            }
            self.env['purchase.order'].create(po_vals)

        self.write({'state': 'po_created'})
        return True

    def action_reject(self):
        return {
            'name': _('Motivo del Rechazo'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_view_purchase_orders(self):
        return {
            'name': _('Órdenes de Compra'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('purchase_request_id', '=', self.id)],
        }


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Línea de Solicitud de Compra'

    request_id = fields.Many2one(
        'purchase.request', string='Solicitud de Compra', ondelete='cascade')

    product_id = fields.Many2one(
        'product.product', string='Producto/Servicio', required=True)

    quantity = fields.Float(string='Cantidad', required=True, default=1.0)

    estimated_price = fields.Float(string='Precio Estimado', compute='_compute_estimated_price', readonly=False,
                                   store=True)

    subtotal = fields.Float(
        string='Subtotal (impuestos incluidos)', compute='_compute_subtotal', store=True)

    suggested_vendor_id = fields.Many2one(
        'res.partner', string='Proveedor Sugerido')

    taxes_id = fields.Many2many('account.tax', string='Impuestos', related='product_id.taxes_id', readonly=True)

    @api.depends('quantity', 'estimated_price', 'product_id', 'taxes_id')
    def _compute_subtotal(self):
        for line in self:
            price = line.estimated_price
            qty = line.quantity

            if line.request_id.requester_id and line.request_id.requester_id.company_id:
                currency = line.request_id.requester_id.company_id.currency_id
            else:
                currency = self.env.company.currency_id

            taxes = line.taxes_id.compute_all(price, currency, qty, product=line.product_id,
                                              partner=line.request_id.requester_id.partner_id)

            line.subtotal = taxes['total_included'] if taxes else qty * price

    @api.depends('product_id')
    def _compute_estimated_price(self):
        for line in self:
            if line.product_id:
                line.estimated_price = line.product_id.standard_price