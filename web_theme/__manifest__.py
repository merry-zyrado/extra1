###################################################################################

{
    'name': 'BTQ Backend Theme',
    'summary': 'Odoo BTQ Theme',
    'version': '16.0.0.0.0',
    'category': 'Themes/Backend', 
    'license': 'LGPL-3', 
    'author': 'BTQ IT',
    'website': 'http://BTQ',
    'depends': [],
    'data': [ ],
    'assets': {
        'web._assets_primary_variables': [
            'web_theme/static/src/scss/primary_variables_custom.scss',
        ],
        'web.assets_backend': [
            "web_theme/static/src/scss/sticky_header.scss",
            'web_theme/static/src/scss/form_view.scss',
            'web_theme/static/src/scss/main.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
