# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

{
    'name': 'Sale Penalty Rules',
    'version': '15.0.1.2',
    'category': 'Sales/Sales',
    'summary': 'Penalty Rules allows you, add interest amount on expired sales orders.',
    'description': """
        - Penalty Rules allows you, add interest amount on expired sales orders
    """,
    'license': 'OPL-1',
    'author': 'Mastermind Software Services',
    'website': 'https://www.mss.mx',
    'depends': ['sale_management'],
    'data': [
        'security/sale_penalty_rules_security.xml',
        'security/ir.model.access.csv',
        'views/sale_penalty_views.xml',
        'views/sale_view.xml'
    ],
    'sequence': 1,
    'installable': True,
    'application': False,
    'auto_install': False
}
