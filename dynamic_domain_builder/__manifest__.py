# -*- coding: utf-8 -*-
{
    'name': "Dynamic Domain Builder",

    'summary': 'Visually build dynamic domains for any relational field (Many2one , Many2many)',

    'description': """
    """,

    'author': "InfoLabWeb",
    'website': "https://infolabweb.odoo.com",
    'license': 'OPL-1',
    'price': 24,
    'currency': 'USD',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'web.assets_backend': [
            'dynamic_domain_builder/static/src/js/context.js',
        ],
    },

}
