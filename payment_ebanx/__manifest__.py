# -*- coding: utf-8 -*-
{
    'name': 'EBANX Payment',
    'summary': 'Payment Acquirer: EBANX Implementation',
    'description': '''Make your transaction through EBANX''',
    'author': 'DRC Systems India Pvt. Ltd.',
    'version': '0.1',
    'category': 'eCommerce',
    'website': 'www.drcsystems.com',
    'depends': ['payment'],
    'data': [
        'views/ebanx_button.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/ebanx_data.xml',
    ],
    'images': ['static/src/img/icon.png'],
    'installable': True,
    'currency': 'EUR',
    'price': '',
}