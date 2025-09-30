# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestPurchaseRequestFunding(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Funding Product',
            'type': 'consu',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
            'standard_price': 120.0,
            'purchase_ok': True,
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Funding Vendor',
            'supplier_rank': 1,
            'company_type': 'company',
        })
        cls.funding_a = cls.env['purchase.request.funding.source'].create({
            'name': 'Fuente A',
            'code': 'FA',
            'sequence': 1,
            'company_id': cls.env.company.id,
        })
        cls.funding_b = cls.env['purchase.request.funding.source'].create({
            'name': 'Fuente B',
            'code': 'FB',
            'sequence': 2,
            'company_id': cls.env.company.id,
        })

    def test_grouping_purchase_orders_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_request_funding_source.po_group_by_funding_source', True)

        request = self.env['purchase.request'].create({
            'date_needed': fields.Date.today(),
            'justification': 'Validar agrupación por fuente de financiamiento.',
            'line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'estimated_price': 100.0,
                    'suggested_vendor_id': self.vendor.id,
                    'funding_source_id': self.funding_a.id,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 2.0,
                    'estimated_price': 200.0,
                    'suggested_vendor_id': self.vendor.id,
                    'funding_source_id': self.funding_b.id,
                }),
            ],
        })

        request.action_create_purchase_order()

        self.assertEqual(request.state, 'po_created')
        self.assertEqual(request.purchase_order_count, 2, 'Debe generarse una OC por fuente de financiamiento distinta.')
        self.assertTrue(all(po.partner_id == self.vendor for po in request.purchase_order_ids))
        self.assertEqual(
            request.purchase_order_count,
            len(set(request.line_ids.mapped('funding_source_id').ids)),
            'El número de órdenes debe coincidir con las fuentes únicas configuradas.',
        )

    def test_funding_breakdown_report_renders_pdf(self):
        request = self.env['purchase.request'].create({
            'date_needed': fields.Date.today(),
            'justification': 'Reporte de desglose por fuente.',
            'line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'estimated_price': 120.0,
                    'suggested_vendor_id': self.vendor.id,
                    'funding_source_id': self.funding_a.id,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 2.0,
                    'estimated_price': 80.0,
                    'suggested_vendor_id': self.vendor.id,
                    'funding_source_id': False,
                }),
            ],
        })

        action = self.env.ref('purchase_request_funding_source.action_report_purchase_request_funding_breakdown')
        pdf_content, _ = action._render_qweb_pdf(request.ids)
        self.assertTrue(pdf_content, 'El reporte PDF de desglose debe generar contenido.')
