# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Backup HR',
    'summary': 'Backup Human Resource',
    'version': '8.0.0.0.1',
    'category': 'Generic Modules',
    'website': 'http://www.kmee.com.br',
    'author': "KMEE, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'depends': [
        'l10n_br_hr_payroll',
    ],
    'data': [
        # 'data/hr_salary_rule_category.xml',
        # 'data/hr_salary_rule.xml',
        # 'data/hr_payroll_structure.xml',
        'views/hr_backup.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_salary_rule.xml',
        # 'views/hr_salary_rule_category.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
