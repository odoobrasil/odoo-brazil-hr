# -*- coding: utf-8 -*-
# Copyright 2017 Sei lá
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Localization HR Allowance',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_holiday',
    ],
    'data': [
        'data/hr_holidays_status_data.xml',
        'data/hr_holidays_data.xml',
        'views/hr_holidays.xml',
    ],
    'demo': [
    ],
}
