# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Validacao da Folha de Pagamento',
    'category': 'ABGF',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainer': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.0.0.1',
    'depends': [
        'l10n_br_hr_holiday',
        'l10n_br_hr_contract',
        'l10n_br_hr_payroll',
        'l10n_br_hr_gerador_holerite',
        'l10n_br_hr_arquivos_governo',
    ],
    'data': [
    ],
    'demo': [
        'demo/funcionarios.yml',
        'demo/contratos.yml',
        'demo/holerites10.yml',
        'demo/holerites11.yml',
    ],
    'test': [
        'tests/test_hr_payslip_10.py',
    ],
    'installable': True,
    'auto_install': False,
}
