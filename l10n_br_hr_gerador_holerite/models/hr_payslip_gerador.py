# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Marco'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
]


class HrPayslipGenerator(models.Model):
    _name = 'hr.payslip.generator'

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string="Contrato",
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )

    ano = fields.Integer(
        string=u'Ano',
        default=datetime.now().year,
    )

    def processar_holerites(self, holerite):
        wd_model = self.env['hr.payslip.worked_days']
        input_model = self.env['hr.payslip.input']

        holerite.set_employee_id()

        res = holerite.onchange_employee_id(
            holerite.date_from, holerite.date_to, holerite.contract_id.id)

        for worked_days_line in res['value']['worked_days_line_ids']:
            worked_days_line['payslip_id'] = holerite.id
            wd_model.create(worked_days_line)

        for input_line in res['value']['input_line_ids']:
            input_line['payslip_id'] = holerite.id
            input_model.create(input_line)

        holerite.compute_sheet()
        holerite.process_sheet()

        return holerite

    @api.multi
    def gerar_holerites(self):
        data_inicio_gerador = \
            str(self.ano) + '-' + str(self.mes_do_ano) + '-01'
        cont = 0

        data_inicio = fields.Date.from_string(data_inicio_gerador)
        data_fim = data_inicio + relativedelta(months=1, days=-1)

        while cont <= 12:

            payslip_dict = {
                'contract_id': self.contract_id.id,
                'date_from': data_inicio,
                'date_to': data_fim,
                'employee_id': self.contract_id.employee_id.id,
                'mes_do_ano': data_inicio.month,
                'ano': data_inicio.year,
            }

            payslip = self.env['hr.payslip'].create(payslip_dict)
            self.processar_holerites(payslip)

            data_inicio += relativedelta(months=1)
            data_fim = data_inicio + relativedelta(months=1, days=-1)
            cont += 1
