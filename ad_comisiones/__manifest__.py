# -*- coding: utf-8 -*-
{
    'name': "Comisiones",
    'summary': 'Modulo para calculo de comisiones',
    'description': 'Calculo de comisiones para las ventas',
    'author': "Mastermind Software Services",
    'website': "https://www.mss.mx",
    'license': 'LGPL-3',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'sale', 'hr'],
    'installable': True,
    'application': True,
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml'
    ],
}
