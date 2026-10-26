# -*- coding: utf-8 -*-

{
    'name': 'Payment Voucher with Analytic Account & Analytic Tag',
    "author": "Edge Technologies",
    'version': '16.0.1.0',
    'live_test_url': "https://youtu.be/UxgQs96sam0",
    "images":['static/description/main_screenshot.png'],
    'summary': "Payment voucher analytic account payment receipt with analytic account account voucher with analytic tag analytic account on payment internal transfer analytic account analytic payment voucher analytic tag payment voucher with cost centre analytic costing",
    'description': """This app helps to allows to configure analytic account and tags in payment then pass automatically in journal entries. user can configure analytic account & tag for both manual and invoice payment.
    
payment voucher with analytic account & analytic tag
payment receipt with analytic account & analytic tag
analytic account
payment receipt analytic tag
payment receipt analytic account
analytic account payment receipt
analytic tag
internal transfer payment
internal transfer analytic account
analytic account internal transfer payment
analytic payment voucher payment receipt analytic account
voucher with analytic account 
voucher analytic tag
payment voucher with cost centre analytics
analytic account payment
create payment with analytic account and tags
add analytic accounting
voucher analytic account
payment voucher analytic tag
payment vouhcer analytical account


    """,
    "license" : "OPL-1",
    'depends': ['base','payment','account'],
    'data': [
            'security/analytic_account_group.xml',
            'views/account_payment_form_inherit.xml',
            ],
    'installable': True,
    'auto_install': False,
    'price': 35,
    'currency': "EUR",
    'category': 'Accounting',
}
