# -*- coding: utf-8 -*-
# Powered by Mastermind Software Services
# © 2022 Mastermind Software Services (<https://www.mss.mx>).

{
    'name': 'Sale Loyalty',
    'version': '15.0.1.2',
    'category': 'Sales/Sales',
    'summary': 'Customers can get rewards option with Discount, Voucher, and Gift, by Loyalty Program Rules then the customer can spend those points to get rewards on purchasing. | sale loyalty points | loyalty point | sale loyalty | loyalty point reward | Loyalty Points | Loyalty Points and Rewards | Gift Rewards | Sale Loyalty Points |  Customer Loyalty Points',
    'description': """
        - Loyalty Points and Rewards on Sale Order
        - Redeem points as per customer requirement
        - Gift the product base on reward rules
        - Give Discount to customer based on the customer loyalty points and based on reward rule
    """,
    'license': 'OPL-1',
    'author': 'Mastermind Software Services',
    'website': 'https://www.mss.mx',
    'depends': ['sale_management'],
    'data': [
        'security/sale_loyalty_security.xml',
        'security/ir.model.access.csv',
        'data/sale_loyalty_data.xml',
        'views/sale_loyalty_views.xml',
        'views/res_config_view.xml',
        'views/sale_view.xml',
        'views/sale_portal_template.xml',
        'views/sale_loyalty_history_views.xml',
        'views/res_partner.xml',
        'report/sale_report.xml',
        'report/points_history_report.xml',
        'wizard/point_selection_wizard_view.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 50,
    'currency': 'EUR'
}
