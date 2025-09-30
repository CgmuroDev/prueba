# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_group_by_funding_source = fields.Boolean(
        string='Agrupar Órdenes por Fuente de Financiamiento',
        config_parameter='purchase_request_funding_source.po_group_by_funding_source',
    )