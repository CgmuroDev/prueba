# -*- coding: utf-8 -*-
{
    'name': "purchase_request_funding_source",

    'summary': "Gestiona las fuentes de financiamiento para solicitudes de compra",

    'description': """
                   Extiende las solicitudes de compra para administrar un catálogo maestro de
                   fuentes de financiamiento por compañía.
                       """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchases',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['purchase_request'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/purchase_request_views.xml',
        'views/purchase_request_source_views.xml',
        'report/purchase_request_funding_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
