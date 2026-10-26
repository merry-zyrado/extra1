{
    "name": "BTQ Web Base",
    "summary": "BTQ Web Based",
    "version": "15.0.0.0.0",
    "category": "Web",
    "website": "https://www.boutiqaat.com/",
    "author": "Boutiqaat",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "web_responsive", "web_refresher", "web_no_bubble", "web_remember_tree_column_width",
                "web_widget_open_tab", "rowno_in_tree",],
    "development_status": "Production/Stable",
    "maintainers": ["Maged"],
    "data":
        [
            "views/login_layout.xml",
        ],
    'assets': {
        'web.assets_frontend': [
            '/btq_web_base/static/src/scss/login_style_3.scss',
        ]
    },
    "sequence": 1,
    'installable': True,
    'application': True,
}
