# -*- coding: utf-8 -*-
from odoo import fields, _
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestPurchaseRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
            'standard_price': 100.0,
            'list_price': 150.0,
            'purchase_ok': True,
        })

        cls.vendor_a = cls.env['res.partner'].create({
            'name': 'Vendor A',
            'supplier_rank': 1,
            'company_type': 'company',
        })
        cls.vendor_b = cls.env['res.partner'].create({
            'name': 'Vendor B',
            'supplier_rank': 1,
            'company_type': 'company',
        })

        cls.group_user = cls.env.ref('purchase_request.group_purchase_request_user')
        cls.group_viewer = cls.env.ref('purchase_request.group_purchase_request_viewer')

        cls.user_requester_1 = cls._create_test_user('requester1', [cls.group_user.id])
        cls.user_requester_2 = cls._create_test_user('requester2', [cls.group_user.id])
        cls.user_viewer = cls._create_test_user('viewer', [cls.group_viewer.id])

    @classmethod
    def _create_test_user(cls, login, group_ids):
        return cls.env['res.users'].create({
            'name': f'{login} Test',
            'login': login,
            'email': f'{login}@example.com',
            'groups_id': [(6, 0, group_ids)],
        })

    def _request_vals(self, line_overrides=None):
        line_default = {
            'product_id': self.product.id,
            'quantity': 2.0,
            'estimated_price': 50.0,
            'suggested_vendor_id': self.vendor_a.id,
        }
        lines = line_overrides or [line_default]
        return {
            'date_needed': fields.Date.today(),
            'justification': 'Necesitamos insumos para pruebas.',
            'line_ids': [(0, 0, dict(line_default, **line)) for line in lines],
        }

    def test_sequence_assigned_on_creation(self):
        request = self.env['purchase.request'].create(self._request_vals())
        self.assertTrue(request.name.startswith('SC/'), 'La secuencia debe usar el prefijo configurado.')
        self.assertNotEqual(request.name, _('New'), 'El nombre no debe permanecer como New.')
        self.assertEqual(request.purchase_order_count, 0)

    def test_create_multiple_purchase_orders_for_distinct_vendors(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_request_funding_source.po_group_by_funding_source', False)

        request = self.env['purchase.request'].create(self._request_vals([
            {
                'product_id': self.product.id,
                'quantity': 5.0,
                'estimated_price': 100.0,
                'suggested_vendor_id': self.vendor_a.id,
            },
            {
                'product_id': self.product.id,
                'quantity': 3.0,
                'estimated_price': 75.0,
                'suggested_vendor_id': self.vendor_b.id,
            },
        ]))

        request.action_create_purchase_order()

        self.assertEqual(request.state, 'po_created')
        self.assertEqual(request.purchase_order_count, 2, 'Debe generarse una OC por proveedor distinto.')
        partner_ids = set(request.purchase_order_ids.mapped('partner_id').ids)
        self.assertSetEqual(partner_ids, {self.vendor_a.id, self.vendor_b.id})

    def test_security_rules_enforced(self):
        request = self.env['purchase.request'].with_user(self.user_requester_1).create(self._request_vals())

        forbidden_requests = self.env['purchase.request'].with_user(self.user_requester_2).search([
            ('id', '=', request.id)
        ])
        self.assertFalse(forbidden_requests, 'Un usuario estándar no debe ver solicitudes de otros usuarios.')

        with self.assertRaises(AccessError):
            request.with_user(self.user_viewer).write({'justification': 'Intento de modificación no permitido.'})

    def test_summary_report_renders_pdf(self):
        request = self.env['purchase.request'].create(self._request_vals())
        action = self.env.ref('purchase_request.action_report_purchase_request_summary')
        pdf_content, _ = action._render_qweb_pdf(request.ids)
        self.assertTrue(pdf_content, 'El reporte PDF de resumen debe generar contenido.')
