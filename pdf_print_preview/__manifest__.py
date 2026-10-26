# -*- encoding: utf-8 -*-

{
    "name": "Pdf Print Preview",
    "version": "1.0",
    "depends": ["web"],
    "author": "itechgroup",
    "category": "web",
    "website": "",
    "summary": """Preview and print PDF report in your browser | Pdf direct preview | Print without Download
    | Quick printer | Easily to print report | Without download PDF File | Preview without Download | Preview report
    | Preview pdf | Odoo direct print | pdf preview | report Preview | PDF Viewer | report Viewer | PDF
    """,
    "description": """ """,
    "support": "support@itechgroup.info",
    "data": [
        # "views/res_users.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "pdf_print_preview/static/src/scss/dialog.scss",
            "pdf_print_preview/static/src/scss/content.scss",
            "pdf_print_preview/static/src/js/dialog.js",
            "pdf_print_preview/static/src/js/pdf_preview.js",
            "pdf_print_preview/static/src/xml/*.xml",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "license": "OPL-1",
    "currency": "EUR",
    "price": 25.99
}
