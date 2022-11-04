# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

{
    'name': 'Sale Return Products',
    'version': '15.0.1.2',
    'category': 'Sales/Sales',
    'summary': 'Customers can return products on Sales Order',
    'description': """
        - Customers can return products on Sales Order
    """,
    'license': 'OPL-1',
    'author': 'Mastermind Software Services',
    'website': 'https://www.mss.mx',
    'depends': ['sale_management'],
    'data': [
        'security/sale_order_return_security.xml',
        'security/ir.model.access.csv',
        'views/sale_view.xml'
    ],
    #'images': ['static/description/banner.jpg'],
    'sequence': 1,
    'installable': True,
    'application': False,
    'auto_install': False
    #'price': 50,
    #'currency': 'EUR'
}
