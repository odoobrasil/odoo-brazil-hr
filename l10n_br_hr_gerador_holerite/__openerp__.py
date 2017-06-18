# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Localization HR Payroll Generator',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_hr_payroll',
    ],
    'data': [
        'views/hr_payslip_gerador.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
