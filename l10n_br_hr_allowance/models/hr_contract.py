# -*- coding: utf-8 -*-
# Copyright 2017 Sei lá
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime


class HrContract(models.Model):
    _inherit = 'hr.contract'

    abonos = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='contrato_id',
        string='Abonos de faltas'
    )

    @api.multi
    def gerar_credito_abonos(self):
        dominio = [
            '|',
            ('date_end', '=', False),
            ('date_end', '>', fields.Date.today()),
        ]
        contratos_ativos = self.env['hr.contract'].search(dominio)
        abono_status_id = self.env.ref(
            'l10n_br_hr_allowance.holiday_status_abono').id
        historico_abono_status_id = self.env.ref(
            'l10n_br_hr_allowance.holiday_status_historico_abono').id
        for contrato in contratos_ativos:
            if contrato.abonos:
                abonos = self.env['hr.holidays'].search([
                    ('contrato_id.id', '=', contrato.id),
                    ('holiday_status_id', '=', abono_status_id),
                ])
                soma = 0
                for abono in abonos:
                    soma += abono.number_of_days
                    abono.holiday_status_id = historico_abono_status_id
                if soma > 0:
                    contrato.abonos.number_of_days_temp -= soma
            contrato.adicionar_abonos()

    def adicionar_abonos(self):
        abono_status_id = self.env.ref(
            'l10n_br_hr_allowance.holiday_status_abono').id
        abono = self.env['hr.holidays'].create({
            'name': 'Faltas abonadas %s'
                    % datetime.now().year,
            'contrato_id': self.id,
            'employee_id': self.employee_id.id,
            'holiday_status_id': abono_status_id,
            'type': 'add',
            'holiday_type': 'employee',
            'number_of_days_temp': 5,
            'ano': datetime.now().year,
        })
        abono.state = 'validate'
        self.abonos = abono

    @api.model
    def create(self, vals):
        contrato = super(HrContract, self).create(vals)
        contrato.adicionar_abonos()
        return contrato
