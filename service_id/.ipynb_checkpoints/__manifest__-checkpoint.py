# -*- coding: utf-8 -*-
{
    'name': "service_id",

    'summary': """
        Add Service ID to subscriptions and invoices""",

    'description': """
        Add Service ID to subscriptions and invoices
    """,

    'author': "Logosnet Services Limited, Yiannis Stavrou",
    'website': "http://www.logosnet.cy.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '15.0.3',

    # any module necessary for this one to work correctly
    'depends': ['sale_subscription'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/subscription_portal_templates.xml',
        'views/report_invoice.xml',
        'views/sale_service_details.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
