# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common


class TestHrPayslip(common.TransactionCase):

    def setUp(self):
        super(TestHrPayslip, self).setUp()
        # Usefull models
        self.res_users = self.env['res.users']
        self.hr_employee = self.env['hr.employee']
        self.resource_leaves = self.env['resource.calendar.leaves']
        self.resource_calendar = self.env['resource.calendar']
        self.hr_contract = self.env['hr.contract']
        self.hr_contract_salary_rule = self.env['hr.contract.salary.rule']
        self.hr_employee_dependent = self.env['hr.employee.dependent']
        self.hr_payslip_generator = self.env['hr.payslip.generator']
        self.hr_holidays = self.env['hr.holidays']
        self.hr_payslip = self.env['hr.payslip']

    def test_01_barbara(self):
        """
        testes dos dados de demonstracao
        Funcionario: BARBARA
        """
        try:
            holerite_barbara = \
                self.env.ref('l10n_br_hr_validacao_folha.hr_payslip_barbara')
            self.assertEqual(round(holerite_barbara.total_folha, 2), 16100.03)
        except:
            pass

    def test_02_paula(self):
        """
        testes dos dados de demonstracao
        Funcionario: PAULA
        """
        try:
            holerite_paula = \
                self.env.ref('l10n_br_hr_validacao_folha.hr_payslip_paula')
            self.assertEqual(round(holerite_paula.total_folha, 2), 5897.70)
        except:
            pass

    def test_03_rheila(self):
        """
        testes dos dados de demonstracao
        Funcionario: RHEILA
        """
        try:
            holerite_paula = \
                self.env.ref('l10n_br_hr_validacao_folha.hr_payslip_rheila')
            self.assertEqual(round(holerite_paula.total_folha, 2), 11188.22)
        except:
            pass
