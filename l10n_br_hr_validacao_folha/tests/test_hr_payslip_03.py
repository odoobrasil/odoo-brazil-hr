# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from openerp import fields
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

        group_employee_id = self.ref('base.group_user')

        # Test users to use through the various tests
        self.user_hruser_id = self.res_users.create({
            'name': 'Hr User',
            'login': 'hruser',
            'alias_name': 'User Mileo',
            'email': 'hruser@email.com',
            'groups_id': [(6, 0, [group_employee_id])],
        })

        self.employee_hr_user_id = self.hr_employee.create({
            'name': 'Employee Luiza',
            'user_id': self.user_hruser_id.id,
        })
        # calendario padrao nacional
        self.nacional_calendar_id = self.resource_calendar.create({
            'name': 'Calendario Nacional',
            'country_id': self.env.ref("base.br").id,
        })
        # create feriado para calendario nacional
        self.holiday_nacional_01 = self.resource_leaves.create({
            'name': 'Feriado em Janeiro 01',
            'date_from': fields.Datetime.from_string('2017-01-08 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-08 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })
        self.resource_leaves.create({
            'name': 'Feriado em Janeiro 02',
            'date_from': fields.Datetime.from_string('2017-03-18 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-03-18 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
            'leave_type': 'F',
            'abrangencia': 'N',
        })

    def criar_falta_nao_remunerada(self):
        # create falta funcionario
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_unjustified_absence')
        holiday_id = self.hr_holidays.create({
            'name': 'Falta Injusticada',
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_hr_user_id.id,
            'date_from': fields.Datetime.from_string('2017-01-10 07:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-10 17:00:00'),
            'number_of_days_temp': 1,
            'payroll_discount': True,
        })
        holiday_id.holidays_validate()

    def criar_dependentes(self, funcionario, quantidade):
        while (quantidade > 0):
            funcionario.have_dependent = True
            tipo_dependente = self.env.ref('l10n_br_hr.l10n_br_dependent_3')
            self.hr_employee_dependent.create({
                'dependent_name':
                    'Filho do ' + funcionario.name + str(quantidade),
                'dependent_dob': '2000-01-01',
                'dependent_type_id': tipo_dependente.id,
                'employee_id': funcionario.id,
                'dependent_verification': True,
            })
            quantidade -= 1

    def criar_funcionario(self, nome, quantidade_dependentes=0):
        funcionario = self.hr_employee.create({
            'name': nome,
        })
        if quantidade_dependentes:
            self.criar_dependentes(funcionario, quantidade_dependentes)
        return funcionario

    def criar_contrato(self, name, employee_id, wage, struct_id, date_start):
        contrato_id = self.hr_contract.create({
            'name': name,
            'employee_id': employee_id.id,
            'wage': wage,
            'struct_id': struct_id.id,
            'date_start': date_start,
        })
        return contrato_id

    def criar_rubricas_especificas(self, rubrica, date_start, specific_qty,
                                   specific_amount, contract_id,
                                   date_stop=datetime.date.today()):
        if rubrica == 'rubrica_saude':
            rule_id = self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_PLANO_SAUDE')
        elif rubrica == 'rubrica_VA':
            rule_id = self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_VA_VR')
        elif rubrica == 'rubrica_creche':
            rule_id = self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_REMBOLSO_AUXILIO_CRECHE')
        elif rubrica == 'rubrica_ligacao':
            rule_id = self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_DESCONTO_LIGACOES')
        elif rubrica == 'rubrica_contribuicao_sindical':
            rule_id = self.env.ref(
                'l10n_br_hr_payroll.hr_salary_rule_CONTRIBUICAO_SINDICAL')
        else:
            return False

        rubrica_especifica = self.hr_contract_salary_rule.create({
            'rule_id': rule_id.id,
            'date_start': date_start,
            'specific_quantity': specific_qty,
            'specific_amount': specific_amount,
            'contract_id': contract_id.id,
            'date_stop': date_stop,
        })
        return rubrica_especifica

    def atribuir_ferias(self, contrato, inicio_ferias,
                        fim_ferias, dias_ferias, dias_abono):
        """
        Atribui férias ao funcionário.
        Cria um holidays nos dias que o funcionario ira gozar as ferias e em
        seguida cria um holerite de férias para o funcionário.
        """
        # Buscar periodo Aquisitivo de acordo com os dias de ferias gozadas
        holiday_periodo_aquisitivo = self.buscar_periodo_aquisitivo(
            contrato, inicio_ferias, fim_ferias)

        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation'
        )

        # Solicitacao de férias do funcionario
        ferias = self.hr_holidays.create({
            'name': 'Ferias Do ' + contrato.employee_id.name,
            'type': 'remove',
            'parent_id': holiday_periodo_aquisitivo.id,
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': contrato.employee_id.id,
            'vacations_days': dias_ferias,
            'sold_vacations_days': dias_abono,
            'number_of_days_temp': dias_ferias + dias_abono,
            'date_from': inicio_ferias,
            'date_to': fim_ferias,
            'contrato_id': contrato.id,
        })

        # Chamando Onchange manualmente para setar o controle de férias
        ferias._compute_contract()

        # Chamando Onchange manualmente para setar datas de inicio e fim
        ferias.setar_datas_core()

        # Aprovacao da solicitacao do funcionario
        ferias.holidays_validate()

        # Gerar holerites do peŕiodo Aquisitivo
        self.gerar_12_holerites(contrato, 1, 2016)

        estrutura_ferias = \
            self.env.ref('l10n_br_hr_payroll.hr_salary_structure_FERIAS')

        # Criar Holerite de Férias
        holerite_ferias = self.hr_payslip.create({
            'tipo_de_folha': 'ferias',
            'periodo_aquisitivo':
                holiday_periodo_aquisitivo.controle_ferias.id,
            'contract_id': contrato.id,
            'employee_id': contrato.employee_id.id,
            'struct_id': estrutura_ferias.id,
            'holidays_ferias': ferias.id,
            'date_from': inicio_ferias,
            'date_to': fim_ferias,
        })

        holerite_ferias._compute_set_dates()
        holerite_ferias.compute_sheet()
        holerite_ferias.process_sheet()

        return holerite_ferias

    def buscar_periodo_aquisitivo(self, contrato, inicio_ferias, fim_ferias):
        for controle_ferias in contrato.vacation_control_ids:
            if controle_ferias.inicio_concessivo < inicio_ferias and \
               controle_ferias.fim_concessivo > fim_ferias:
                if not controle_ferias.hr_holiday_ids:
                    controle_ferias.gerar_holidays_ferias()
                holidays = controle_ferias.hr_holiday_ids
                for holiday in holidays:
                    if holiday.type == 'add':
                        return holiday

    def gerar_12_holerites(self, contrato, mes_do_ano, ano):
        # Gerar holerites do periodo aquisitivo
        gerador_holerites = self.hr_payslip_generator.create({
            'contract_id': contrato.id,
            'mes_do_ano': mes_do_ano,
            'ano': ano,
        })
        gerador_holerites.gerar_holerites()

    def gerar_holerite_normal(self, contrato, mes_do_ano, ano):
        # Criar Holerite Normal
        holerite_normal = self.hr_payslip.create({
            'tipo_de_folha': 'normal',
            'contract_id': contrato.id,
            'employee_id': contrato.employee_id.id,
            'mes_do_ano': mes_do_ano,
            'ano': ano,
        })
        holerite_normal._compute_set_dates()
        holerite_normal.compute_sheet()
        holerite_normal.process_sheet()
        return holerite_normal

    def test_00_jennifer(self):
        """
        Funcionario: JENNIFER
        Salario Base: 11615.60
        Data Admissao: 02/01/14
        Rubricas Especificas:
            - Reembolso Plano de Saude - 400.00
            - Reembolso Auxílio Creche - 370.71
            - VA/VR                    - 6.04
            - Desconto Ligações        - 40,53
            - Contribuição Sindical    - 387,19
        Dependentes: 3
        Ferias: 13/10/16 - 22/10/16
        Abono Pecuniario: 0
        Dias Trabalhados: 20
        Férias Total: R$ 4116.74
        Holerite total: R$ 7050,14
        :return:
        """

        employee_id = self.criar_funcionario('JENNIFER', 3)
        data_admissao = '2014-01-02'
        estrutura_salario = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FUNCAO_COMISSIONADA')

        # Criar Contrato
        contrato = self.criar_contrato(
            'Contrato do JENNIFER', employee_id, 11615.60,
            estrutura_salario, data_admissao)

        # Criar Rubricas especificas do contrato
        self.criar_rubricas_especificas(
            'rubrica_saude', data_admissao, 1, 400.00, contrato)
        self.criar_rubricas_especificas(
            'rubrica_creche', data_admissao, 1, 395.55, contrato)
        self.criar_rubricas_especificas(
            'rubrica_VA', data_admissao, 1, 7.72, contrato)
        self.criar_rubricas_especificas(
            'rubrica_ligacao', data_admissao, 1, 40.53, contrato)
        self.criar_rubricas_especificas(
            'rubrica_contribuicao_sindical',
            data_admissao, 1, 387.19, contrato)

        # Atribuir Holidays de Férias ao funcinario e gerar aviso de ferias
        self.atribuir_ferias(contrato, '2017-03-01', '2017-03-10', 10, 10)

        # Gerar holerite normal ja puxando informações das ferias
        holerite_normal = self.gerar_holerite_normal(contrato, 03, 2017)

        for rubrica in holerite_normal.line_ids:
            if rubrica.total:
                # Proventos
                if rubrica.code == 'SALARIO':
                    self.assertEqual(rubrica.total, 7743.73)
                if rubrica.code == 'REMBOLSO_SAUDE':
                    self.assertEqual(rubrica.total, 400.00)
                if rubrica.code == 'REMBOLSO_AUXILIO_CRECHE':
                    self.assertEqual(rubrica.total, 395.55)
                if rubrica.code == 'FERIAS':
                    self.assertEqual(rubrica.total, 3871.87)
                if rubrica.code == '1/3_FERIAS':
                    self.assertEqual(rubrica.total, 1290.62)
                if rubrica.code == 'ABONO_PECUNIARIO':
                    self.assertEqual(rubrica.total, 3871.87)
                if rubrica.code == '1/3_ABONO_PECUNIARIO':
                    self.assertEqual(rubrica.total, 1290.62)

                # Deduções
                if rubrica.code == 'CONTRIBUICAO_SINDICAL':
                    self.assertEqual(rubrica.total, 387.19)
                if rubrica.code == 'VA/VR':
                    self.assertEqual(rubrica.total, 7.72)
                if rubrica.code == 'DESCONTO_LIGACOES_TELEFONICAS':
                    self.assertEqual(rubrica.total, 40.53)
                # Adiantamento do 13 Salario esta sendo cobrado junto ?
                # if rubrica.code == 'PAGAMENTO_FERIAS':
                #     self.assertEqual(rubrica.total, 15295.22)

                # INSS Mensal
                if rubrica.code == 'INSS':  # INSS Mensal - Teto
                    self.assertEqual(rubrica.total, 40.57)
                # INSS FERIAS
                if rubrica.code == 'INSS_FERIAS' and rubrica.valor_deducao:
                    self.assertEqual(rubrica.total, 567.87)

                # IRRF
                if rubrica.code == 'IRPF':
                    self.assertEqual(rubrica.total, 1092.60)
                # IRRF FERIAS
                if rubrica.code == 'IRPF_FERIAS':
                    self.assertEqual(rubrica.total, 269.69)

                # Referências de cálculos
                if rubrica.code == 'BASE_INSS_FERIAS':  # BASE_INSS FERIAS
                    # BASE_INSS_FERIAS = FERIAS + 1/3_FERIAS
                    BASE_INSS_FERIAS = 3871.87 + 1290.62
                    self.assertEqual(rubrica.total, BASE_INSS_FERIAS)
                if rubrica.code == 'BASE_IRPF_FERIAS':  # BASE_IRRF FERIAS
                    # BASE_IRRF_FERIAS = BASE_INSS_FERIAS -INSSFerias - Depend.
                    BASE_IRRF_FERIAS = BASE_INSS_FERIAS - 567.87 - 568.77
                    self.assertEqual(rubrica.total, BASE_IRRF_FERIAS)

                if rubrica.code == 'BASE_INSS':  # BASE_INSS
                    # BASE_INSS = SALARIO
                    BASE_INSS = 7743.73
                    self.assertEqual(rubrica.total, BASE_INSS)
                if rubrica.code == 'BASE_IRPF':   # BASE_IRRF
                    # BASE_IRRF = (Salario - INSS MENSAL- Dependen
                    BASE_IRRF = round(7743.73 - 40.57 - 568.77, 2)
                    self.assertEqual(rubrica.total, BASE_IRRF)

        # Valor Liquido do holerite
        # holerite_normal = 6970.670000000007
        # self.assertEqual(holerite_normal.total_folha, 6970.68)

    def test_02_linda(self):
        """
        Funcionario: Linda
        Salario Base: 7.866,22
        Data Admissao: 2014-09-08'
        Rubricas Especificas:
            - Reembolso Plano de Saude - 309.77
            - VA/VR                    - 6.60
            - Creche                   - 395.55
            - Contibuição Sindical     - 262.21
        Dependentes: 1
        Holerite total: R$ 6.618,78
        """
        employee_id = self.criar_funcionario('LINDA', 1)
        data_admissao = '2014-09-08'
        estrutura_salario = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FUNCAO_COMISSIONADA')

        # Criar Contrato
        contrato = self.criar_contrato(
            'Contrato da LINDA', employee_id, 7866.22,
            estrutura_salario, data_admissao)

        # Criar Rubricas especificas do contrato
        self.criar_rubricas_especificas(
            'rubrica_saude', data_admissao, 1, 309.77, contrato)
        self.criar_rubricas_especificas(
            'rubrica_creche', data_admissao, 1, 395.55, contrato)
        self.criar_rubricas_especificas(
            'rubrica_VA', '2017-04-01', 1, 6.60, contrato)
        self.criar_rubricas_especificas(
            'rubrica_VA', '2017-03-01', 1, 7.72, contrato,
            date_stop='2017-03-31')

        # Gerar holerite normal ja puxando informações das ferias
        holerite_normal = self.gerar_holerite_normal(contrato, 3, 2017)

        for rubrica in holerite_normal.line_ids:

            if rubrica.total:

                # Proventos
                if rubrica.code == 'SALARIO':
                    self.assertEqual(rubrica.total, 7866.22)
                if rubrica.code == 'REMBOLSO_SAUDE':
                    self.assertEqual(rubrica.total, 309.77)
                if rubrica.code == 'REMBOLSO_AUXILIO_CRECHE':
                    self.assertEqual(rubrica.total, 395.55)

                # Deduções
                if rubrica.code == 'VA/VR':
                    self.assertEqual(rubrica.total, 7.72)
                if rubrica.code == 'CONTRIBUICAO_SINDICAL':
                    self.assertEqual(rubrica.total, 262.21)
                if rubrica.code == 'INSS':  # INSS
                    self.assertEqual(rubrica.total, 608.44)
                if rubrica.code == 'IRPF':  # IRRF
                    self.assertEqual(rubrica.total, 1074.39)

                # Referências de cálculos
                if rubrica.code == 'BASE_INSS':  # BASE_INSS
                    # BASE_INSS = SALARIO
                    BASE_INSS = 7866.22
                    self.assertEqual(rubrica.total, BASE_INSS)
                if rubrica.code == 'BASE_IRPF':   # BASE_IRRF
                    # BASE_IRRF = BASE_INSS - INSS - Dependen
                    BASE_IRRF = round(BASE_INSS - 608.44 - 189.59, 2)
                    self.assertEqual(rubrica.total, BASE_IRRF)

        # Valor Liquido do holerite
        # self.assertEqual(holerite_normal.total_folha, 6618.78)
