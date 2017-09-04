# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import time

from openerp import api, models, fields, _
from openerp.exceptions import Warning
from openerp.tools import float_compare, float_is_zero

NOME_LANCAMENTO = {
    'normal': u'Holerite Normal - ',
    'rescisao': u'Rescisão - ',
    'ferias': u'Férias - ',
    'decimo_terceiro': u'Décimo Terceiro - ',
    'aviso_previo': u'Aviso Prévio - ',
    'provisao_ferias': u'Provisão de Férias - ',
    'provisao_decimo_terceiro': u'Provisão de Décimo Terceiro - ',
}


class L10nBrHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def _buscar_diario_fopag(self):
        if self.env.context.get('params'):
            return self.env.ref(
                "l10n_br_hr_payroll_account.payroll_account_journal").id
        return self.env["account.journal"]

    @api.multi
    def _buscar_lancamentos(self):
        for payslip in self:
            if payslip.id:
                payslip.move_lines_id = self.env['account.move.line'].search(
                    [
                        ('payslip_id', '=', payslip.id)
                    ]
                )

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Accounting Entry',
    )

    move_lines_id = fields.One2many(
        comodel_name='account.move.line',
        string=u'Lançamentos',
        compute=_buscar_lancamentos
    )

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string=u"Diário",
        default=_buscar_diario_fopag
    )

    @api.multi
    def _verificar_lancamentos_anteriores(self, tipo_folha, period_id):
        for payslip in self:
            move_id = self.env['account.move'].search(
                [
                    ('name', 'like', NOME_LANCAMENTO[tipo_folha]),
                    ('name', 'like', payslip.contract_id.nome_contrato),
                    ('period_id', '!=', period_id)
                ],
                limit=1
            )
            if not move_id:
                return False
            else:
                return move_id

    @api.multi
    def _valor_lancamento_anterior_rubrica(self, move_id, rubrica_id):
        for line in move_id.line_id:
            if rubrica_id.id == line.id:
                return line.debit, line.credit, line.period_id
        return 0, 0, 0

    @api.multi
    def _buscar_contas(self, salary_rule):
        if self.tipo_de_folha == "provisao_ferias":
            return salary_rule.provisao_ferias_account_debit, salary_rule.\
                provisao_ferias_account_credit
        elif self.tipo_de_folha == "provisao_decimo_terceiro":
            return salary_rule.provisao_13_account_debit, salary_rule.\
                provisao_13_account_credit
        elif self.tipo_de_folha == "normal":
            return salary_rule.holerite_normal_account_debit, salary_rule.\
                holerite_normal_account_credit
        else:
            return False, False

    @api.multi
    def processar_folha(self):
        if self.journal_id:
            move_obj = self.env['account.move']
            period_obj = self.env['account.period']
            precision = self.env['decimal.precision'].precision_get('Payroll')
            timenow = time.strftime('%Y-%m-%d')

            for slip in self:
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                period_id = period_obj.find(slip.date_to)
                if slip.move_id:
                    move = slip.move_id
                    move_lines = self.env['account.move.line'].search(
                        [
                            ('move_id', '=', move.id)
                        ]
                    )
                    for line in move_lines:
                        line.unlink()
                else:
                    name = \
                        NOME_LANCAMENTO[slip.tipo_de_folha] \
                        + str(slip.mes_do_ano) + "/" + str(slip.ano) \
                        + " - " + slip.contract_id.nome_contrato
                    move = {
                        'name': name,
                        'display_name': name,
                        'narration': name,
                        'date': slip.date_from,
                        'ref': slip.number,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id.id,
                        'payslip_id': slip.id,
                    }
                move_anterior_id = self._verificar_lancamentos_anteriores(
                    slip.tipo_de_folha, period_id.id
                )
                for line in slip.details_by_salary_rule_category:
                    if line.total:
                        debit_account_id, credit_account_id = \
                            slip._buscar_contas(line.salary_rule_id)
                        if debit_account_id or credit_account_id:
                            amt = slip.credit_note and - \
                                line.total or line.total
                            if float_is_zero(amt, precision_digits=precision):
                                continue
                            if slip.tipo_de_folha in [
                                'provisao_ferias', 'provisao_decimo_terceiro'
                            ]:
                                if move_anterior_id:
                                    debito, credito, \
                                        periodo_anterior_id = self.\
                                        _valor_lancamento_anterior_rubrica(
                                            move_anterior_id,
                                            line.salary_rule_id
                                        )
                                    if debito or credito:
                                        line_anterior = (0, 0, {
                                            'name': line.name + " (Anterior)",
                                            'date': timenow,
                                            'account_id':
                                                debit_account_id.id if debito
                                                else credit_account_id.id,
                                            'journal_id': slip.journal_id.id,
                                            'period_id':
                                                periodo_anterior_id.id,
                                            'debit': credito or 0.0,
                                            'credit': debito or 0.0,
                                            'payslip_id': slip.id,
                                        })
                                        line_ids.append(line_anterior)
                                        if debito:
                                            debit_sum += \
                                                line_anterior[2]['debit'] - \
                                                line_anterior[2]['credit']
                                        else:
                                            credit_sum += \
                                                line_anterior[2]['credit'] - \
                                                line_anterior[2]['debit']
                            if debit_account_id and slip.tipo_de_folha not in [
                                'provisao_ferias', 'provisao_decimo_terceiro'
                            ]:
                                debit_line = (0, 0, {
                                    'name': line.name,
                                    'date': timenow,
                                    'account_id': debit_account_id.id,
                                    'journal_id': slip.journal_id.id,
                                    'period_id': period_id.id,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,
                                    'payslip_id': slip.id,
                                })
                                line_ids.append(debit_line)
                                debit_sum += \
                                    debit_line[2]['debit'] - debit_line[2][
                                        'credit']
                            if credit_account_id:
                                credit_line = (0, 0, {
                                    'name': line.name,
                                    'date': timenow,
                                    'account_id': credit_account_id.id,
                                    'journal_id': slip.journal_id.id,
                                    'period_id': period_id.id,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,
                                    'payslip_id': slip.id,
                                })
                                line_ids.append(credit_line)
                                credit_sum += \
                                    credit_line[2]['credit'] - credit_line[2][
                                        'debit']
                        else:
                            pass
                            # raise exceptions.Warning(
                            #     "Não foi selecionada nenhuma conta de
                            #      crédito ou débito para a rúbrica ",
                            # (line.display_name)
                            # )
                if float_compare(
                        credit_sum, debit_sum, precision_digits=precision
                ) == -1:
                    acc_id = slip.journal_id.default_credit_account_id.id
                    if not acc_id:
                        raise Warning(_('Configuration Error!'),
                                      _('The Expense Journal "%s" has not '
                                        'properly configured the '
                                        'Credit Account!'
                                        ) % slip.journal_id.name)
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'date': timenow,
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id.id,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                        'payslip_id': slip.id,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(
                        debit_sum, credit_sum, precision_digits=precision
                ) == -1:
                    acc_id = slip.journal_id.default_debit_account_id.id
                    if not acc_id:
                        raise Warning(_('Configuration Error!'),
                                      _('The Expense Journal "%s" '
                                        'has not properly configured'
                                        ' the Debit Account!'
                                        ) % slip.journal_id.name)
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'date': timenow,
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id.id,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                        'payslip_id': slip.id,
                    })
                    line_ids.append(adjust_debit)
                if not slip.move_id:
                    move.update({'line_id': line_ids})
                    move_id = move_obj.create(move)
                else:
                    for line in line_ids:
                        line[2].update({'move_id': slip.move_id.id})
                        self.env['account.move.line'].create(line[2])
                    move_id = slip.move_id
                self.write({'move_id': move_id.id})
                if slip.journal_id.entry_posted:
                    move_obj.post(move_id)
        else:
            raise Warning(
                _('Erro!'),
                _('É preciso selecionar um diário para realizar '
                  'a contabilização!')
            )
