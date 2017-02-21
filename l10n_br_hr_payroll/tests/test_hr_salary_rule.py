# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common


class TestHrPayslipSalaryRules(common.TransactionCase):

    def setUp(self):
        super(TestHrPayslipSalaryRules, self).setUp()
        self.wd_model = self.env['hr.payslip.worked_days']
        self.input_model = self.env['hr.payslip.input']

        self.holerite_eugenio = self.generate_payslip(
            self.env.ref('l10n_br_hr_payroll.hr_payslip_eugenio_10'))

        self.amount_rules = {
            'SALARIO': 29483.08,
            'REMBOLSO_SAUDE': 400,
            'VA/VR': 6.04,
            'LIQUIDO': 22224.66,
            'BRUTO': 29883.08,
            'INSS': 570.88,
            'FGTS': 2358.65,
            'IRPF': 7081.50,
        }

    def generate_payslip(self, holerite):
        holerite.set_employee_id()
        res = holerite.onchange_employee_id(
            holerite.date_from, holerite.date_to, holerite.contract_id.id)

        for worked_days_line in res['value']['worked_days_line_ids']:
            worked_days_line['payslip_id'] = holerite.id
            self.wd_model.create(worked_days_line)

        for input_line in res['value']['input_line_ids']:
            input_line['payslip_id'] = holerite.id
            self.input_model.create(input_line)

        holerite.compute_sheet()
        return holerite

    def get_line(self, code):
        lines = self.holerite_eugenio.line_ids
        for line in lines:
            if line.code == code:
                return line

    def test_01_payslip_eugenio_rule_SALARIO(self):
        line = self.get_line('SALARIO')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_02_payslip_eugenio_rule_REMBOLSO_SAUDE(self):
        line = self.get_line('REMBOLSO_SAUDE')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_03_payslip_eugenio_rule_VA_VR(self):
        line = self.get_line('VA/VR')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_04_payslip_eugenio_rule_LIQUIDO(self):
        line = self.get_line('LIQUIDO')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_05_payslip_eugenio_rule_BRUTO(self):
        line = self.get_line('BRUTO')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_06_payslip_eugenio_rule_INSS(self):
        line = self.get_line('INSS')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_07_payslip_eugenio_rule_FGTS(self):
        line = self.get_line('FGTS')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))

    def test_08_payslip_eugenio_rule_IRPF(self):
        line = self.get_line('IRPF')
        self.assertEqual(
            line.total, self.amount_rules.get(line.code),
            'ERRO no Calculo da Rubrica de %s' % (line.code))
