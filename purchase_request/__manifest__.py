{
    'name': "Purchase Request Management",
    'summary': "Manage internal purchase requests before creating Purchase Orders.",
    'description': """
                                              Este módulo permite a los empleados crear solicitudes de compra.
                                              - Flujo de trabajo de aprobación.
                                              - Generación automática de órdenes de compra.
                                          """,
    'author': "Carlos Manuel",
    'website': "https://www.yourcompany.com",
    'category': 'Purchases',
    'version': '0.1',
    'depends': ['base', 'purchase', 'hr', 'mail'],
    'data': [
        'security/purchase_request_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/mail_template_data.xml',
        'views/purchase_request_views.xml',
        'views/purchase_order_views.xml',
        'views/purchase_request_dashboard.xml',
        'report/purchase_request_report.xml',
        'wizard/rejection_wizard_views.xml',
    ],
    'application': True,
}
