# -*- coding: utf-8 -*-
{
    'name': "mnk_theme",

    'summary': """
        mnk theme for odoo
    """,

    'description': """
        mnk theme for odoo
        nice theme
        awesome theme
        beautiful theme
        good theme
        best theme
        app board
        odoo theme
        owl theme 
        multi mode theme
        free theme
        multi style theme
        button style theme
        free theme
    """,

    'author': "Funenc Odoo",
    'website': "https://www.openerpnext.com",
    'live_test_url': 'https://mnk.openerpnext.com',

    'images': [
        'static/description/anita_description.png', 
        'static/description/anita_screenshot.png'
    ],

    'category': 'theme/backend',
    'version': '16.0.0.2',
    'license': 'OPL-1',
    'depends': ['base'],

    'data': [],

    'assets': {
        'web.assets_backend': [
            # appbar
            'mnk_theme/static/src/css/anita_variables.scss',
'mnk_theme/static/src/css/_hover.scss',
            'mnk_theme/static/src/css/_buttons.scss',
            'mnk_theme/static/src/css/anita_buttons.scss',
            'mnk_theme/static/src/css/anita_form_view.scss',
            # 'mnk_theme/static/src/components/app_bar/*',
            # # app board
            # 'mnk_theme/static/src/components/app_board/*',
            # # navbar
           'mnk_theme/static/src/components/navbar/*',
            # # webclient
            # 'mnk_theme/static/src/mnk_webclient.js',
            # 'mnk_theme/static/src/mnk_webclient.xml',
        ]
    }
}
