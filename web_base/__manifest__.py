{
    "name": "Web Base",
    "summary": "Web Based",
    "version": "16.0.0.0.0",
    "category": "Web",
    "website": "https://www.boutiqaat.com/",
    "author": "Boutiqaat",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "web_responsive", "web_refresher"],
    "maintainers": ["Maged"],
    "data":
        [
            "views/login_layout.xml",
        ],
    'assets': {
        'web.assets_frontend': [
            '/web_base/static/src/scss/login_style_3.scss',
        ]
    },
    "sequence": 1,
    'installable': True,
    'application': True,
}
