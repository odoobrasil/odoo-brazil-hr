# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class HrContract(models.Model):

    _inherit = 'hr.contract'

    def buscar_periodo_aquisitivo(self, contrato, inicio_ferias, fim_ferias):
        """
        Método utilizado apenas para testes
        Dado os dias de gozo das férias, o método busca o período aquisitivo
        :param contrato:
        :param inicio_ferias:
        :param fim_ferias:
        :return:
        """
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
        """
        Método utilizado apenas para testes
        Gera 12 holerites normais para determinado contrato apartir da data
        passada como parâmetro
        :param contrato:
        :param mes_do_ano:
        :param ano:
        :return:
        """
        # Gerar holerites do periodo aquisitivo
        gerador_holerites = self.env['hr.payslip.generator'].create({
            'contract_id': contrato.id,
            'mes_do_ano': mes_do_ano,
            'ano': ano,
        })
        gerador_holerites.gerar_holerites()

    def atribuir_ferias(self, inicio_ferias, fim_ferias,
                        dias_ferias, dias_abono):
        """
        Método utilizado apenas para testes
        Atribui férias ao funcionário.
        Cria um holidays nos dias que o funcionario ira gozar as ferias e em
        seguida cria um holerite de férias para o funcionário.
        """
        # Buscar periodo Aquisitivo de acordo com os dias de ferias gozadas
        holiday_periodo_aquisitivo = self.buscar_periodo_aquisitivo(
            self, inicio_ferias, fim_ferias)

        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation'
        )

        ferias_gozadas = self.env['hr.holidays'].search([
            ('date_from', '=', inicio_ferias),
            ('date_to', '=', fim_ferias),
            ('contrato_id', '=', self.id),
            ('employee_id', '=', self.employee_id.id),
        ])

        if ferias_gozadas:
            return False

        ferias = self.env['hr.holidays'].create({
            'name': 'Ferias Do ' + self.employee_id.name,
            'type': 'remove',
            'parent_id': holiday_periodo_aquisitivo.id,
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': self.employee_id.id,
            'vacations_days': dias_ferias,
            'sold_vacations_days': dias_abono,
            'number_of_days_temp': dias_ferias + dias_abono,
            'date_from': inicio_ferias,
            'date_to': fim_ferias,
            'contrato_id': self.id,

        })

        # Chamando Onchange manualmente para setar o controle de férias
        ferias._compute_contract()

        # Chamando Onchange manualmente para setar datas de inicio e fim
        ferias.setar_datas_core()

        # Ajustar nome do holidays
        ferias._compute_name_holiday()

        # Aprovacao da solicitacao do funcionario
        ferias.holidays_validate()

        # Gerar holerites do peŕiodo Aquisitivo
        self.gerar_12_holerites(self, 1, 2015)

        estrutura_ferias = \
            self.env.ref('l10n_br_hr_payroll.hr_salary_structure_FERIAS')

        # Criar Holerite de Férias
        holerite_ferias = self.env['hr.payslip'].create({
            'tipo_de_folha': 'ferias',
            'contract_id': self.id,
            'employee_id': self.employee_id.id,
            'struct_id': estrutura_ferias.id,
            'holidays_ferias': ferias.id,
            'date_from': inicio_ferias,
            'date_to': fim_ferias,
        })

        holerite_ferias._compute_set_dates()
        holerite_ferias.compute_sheet()
        holerite_ferias.process_sheet()

        return holerite_ferias
