# -*- coding: utf-8 -*-
from odoo import fields, models, _


class PurchaseRequestFundingSource(models.Model):
	_name = 'purchase.request.funding.source'
	_description = 'Fuente de Financiamiento'
	_order = 'sequence, name'


	name = fields.Char(string='Nombre', required=True)
	code = fields.Char(string='Código', required=True)
	sequence = fields.Integer(string='Secuencia', default=10, help='Orden de visualización.')
	company_id = fields.Many2one(
		comodel_name='res.company',
		string='Compañía',
		required=True,
		index=True,
		default=lambda self: self.env.company,
		help='Compañía a la que pertenece la fuente de financiamiento.'
	)
	description = fields.Text(string='Descripción')
	active = fields.Boolean(string='Activo', default=True)

	_sql_constraints = [
		(
			'name_company_unique',
			'unique(name, company_id)',
			_('El nombre de la fuente de financiamiento debe ser único por compañía.'),
		),
		(
			'code_company_unique',
			'unique(code, company_id)',
			_('El código de la fuente de financiamiento debe ser único por compañía.'),
		),
	]



