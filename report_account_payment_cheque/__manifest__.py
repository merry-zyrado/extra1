{
    'name': 'Account Payment Cheque',
    'author': 'Mpstafa Elgabry',
    'version': '0.1',
    'summary': 'Account Payment Cheque',
    'sequence': 5,
    'description': """""",
    'category': 'account',
    'depends': ['base', 'account'],
    'data': [
        'views/account_payment_views.xml',
        'reports/action_cheque.xml',
        'reports/template_paid_cheque.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': True,
    'application': True,
    'license': 'LGPL-3',
}
