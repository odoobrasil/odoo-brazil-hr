# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import time

from openerp import api, models, fields, exceptions, _
from openerp.tools import float_compare
from lxml import etree

NOME_LANCAMENTO_LOTE = {
    'provisao_ferias': u'Provisão de Férias em Lote',
    'provisao_decimo_terceiro': u'Provisão de 13 em Lote',
    'normal': u'Folha normal em Lote',
}


class L10nBrHrPayslip(models.Model):
    _inherit = 'hr.payslip.run'

    @api.model
    def _buscar_diario_fopag(self):
        if self.env.context.get('params'):
            return self.env.ref(
                "l10n_br_hr_payroll_account.payroll_account_journal").id
        return self.env["account.journal"]

    @api.multi
    def _buscar_lancamentos(self):
        for payslip_run in self:
            if payslip_run.id:
                payslip_run.move_lines_id = \
                    self.env['account.move.line'].search(
                        [
                            ('payslip_run_id', '=', payslip_run.id)
                        ]
                    )

    provisao_ferias_account_debit = fields.Many2one(
        comodel_name='account.account',
        string='Conta débito provisão de Férias',
    )
    provisao_ferias_account_credit = fields.Many2one(
        comodel_name='account.account',
        string='Conta crédito provisão de Férias',
    )

    provisao_13_account_debit = fields.Many2one(
        comodel_name='account.account',
        string='Conta débito provisão Décimo 13º',
    )
    provisao_13_account_credit = fields.Many2one(
        comodel_name='account.account',
        string='Conta crédito provisão Décimo 13º',
    )
    holerite_normal_account_debit = fields.Many2one(
        comodel_name='account.account',
        string='Conta débito holerite normal',
    )
    holerite_normal_account_credit = fields.Many2one(
        comodel_name='account.account',
        string='Conta crédito holerite normal',
    )
    decimo_13_account_debit = fields.Many2one(
        comodel_name='account.account',
        string='Conta débito Décimo 13º',
    )
    decimo_13_account_credit = fields.Many2one(
        comodel_name='account.account',
        string='Conta crédito Décimo 13º',
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
    def _buscar_contas_lotes(self):
        if self.tipo_de_folha == "normal":
            return self.holerite_normal_account_debit, self.\
                holerite_normal_account_credit
        elif self.tipo_de_folha == "decimo_terceiro":
            return self.decimo_13_account_debit, self.\
                decimo_13_account_credit
        elif self.tipo_de_folha == "provisao_ferias":
            return self.provisao_ferias_account_debit, self.\
                provisao_ferias_account_credit
        elif self.tipo_de_folha == "provisao_decimo_terceiro":
            return self.provisao_13_account_debit, self.\
                provisao_13_account_credit
        else:
            return False, False

    @api.multi
    def _verificar_lancamentos_lotes_anteriores(self, tipo_folha, period_id):
        for payslip in self:
            move_id = self.env['account.move'].search(
                [
                    (
                        'name',
                        'like',
                        NOME_LANCAMENTO_LOTE[tipo_folha]
                    ),
                    (
                        'period_id', '!=', period_id
                    )
                ],
                limit=1
            )
            if not move_id:
                return False
            else:
                return move_id

    @api.multi
    def _valor_lancamento_lote_anterior_rubrica(self, rubrica):
        if self.tipo_de_folha == "normal":
                return \
                    rubrica.salary_rule_id.holerite_normal_account_debit, \
                    rubrica.salary_rule_id.holerite_normal_account_credit
        return 0, 0

    @api.multi
    def _verificar_existencia_conta_rubrica(self, rubrica, tipo_de_folha):
        if tipo_de_folha == "provisao_ferias":
            if rubrica.provisao_ferias_account_debit or \
                    rubrica.provisao_ferias_account_credit:
                return True
        elif tipo_de_folha == "provisao_decimo_terceiro":
            if rubrica.provisao_13_account_debit or \
                    rubrica.provisao_13_account_credit:
                return True
        elif tipo_de_folha == "normal":
            if rubrica.holerite_normal_account_debit or \
                    rubrica.holerite_normal_account_credit:
                return True
        else:
            return False

    @api.multi
    def processar_folha(self):
        if self.journal_id:
            conta_debito, conta_credito = self._buscar_contas_lotes()
#            if conta_debito or conta_credito:

            for payslip_run in self:
                move_obj = self.env['account.move']
                period_obj = self.env['account.period']
                precision = \
                    self.env['decimal.precision'].precision_get('Payroll')
                timenow = time.strftime('%Y-%m-%d')
                period_id = period_obj.find(payslip_run.date_start)
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                if payslip_run.move_id:
                    move = payslip_run.move_id
                    move_lines = self.env['account.move.line'].search(
                        [
                            ('move_id', '=', move.id)
                        ]
                    )
                    for line in move_lines:
                        line.unlink()
                else:
                    name = \
                        NOME_LANCAMENTO_LOTE[payslip_run.tipo_de_folha] + \
                        " - " + str(payslip_run.mes_do_ano) + \
                        "/" + str(payslip_run.ano)
                    move = {
                        'name': name,
                        'display_name': name,
                        'narration': name,
                        'date': payslip_run.date_end,
                        'ref': payslip_run.display_name,
                        'journal_id': payslip_run.journal_id.id,
                        'period_id': period_id.id,
                        'payslip_run_id': payslip_run.id,
                    }
                rubricas = {}
                for payslip in self.slip_ids:
                    for line in payslip.details_by_salary_rule_category:
                        if payslip_run._verificar_existencia_conta_rubrica(
                                line.salary_rule_id,
                                payslip_run.tipo_de_folha
                        ):
                            if not rubricas.get(line.name):
                                rubricas.update({line.name: line})
                            else:
                                rubricas[line.name].total += line.total
                move_anterior_id = \
                    self._verificar_lancamentos_lotes_anteriores(
                        payslip_run.tipo_de_folha, period_id.id
                    )
                for rubrica in rubricas:
                    debito, credito = \
                        self._valor_lancamento_lote_anterior_rubrica(
                            rubricas[rubrica]
                        )
                    if payslip_run.tipo_de_folha in [
                        'provisao_ferias',
                        'provisao_decimo_terceiro'
                    ]:
                        if move_anterior_id:
                            if debito or credito:
                                line_anterior = (0, 0, {
                                    'name': rubrica + " (Anterior)",
                                    'date': timenow,
                                    'account_id':
                                        conta_debito.id if debito else
                                        conta_credito.id,
                                    'journal_id':
                                        payslip_run.journal_id.id,
                                    'period_id': period_id.id,
                                    'debit': credito or 0.0,
                                    'credit': debito or 0.0,
                                    'payslip_run_id': payslip_run.id,
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
                    if credito:
                        credit_line = (0, 0, {
                            'name': rubrica,
                            'date': timenow,
                            'account_id': credito.id,
                            'journal_id': payslip_run.journal_id.id,
                            'period_id': period_id.id,
                            'debit': 0.0,
                            'credit': rubricas[rubrica].total,
                            'payslip_run_id': payslip_run.id,
                        })
                        line_ids.append(credit_line)
                        credit_sum += \
                            credit_line[2]['credit'] - credit_line[2][
                                'debit']
                    if debito:
                        debit_line = (0, 0, {
                            'name': rubrica,
                            'date': timenow,
                            'account_id': debito.id,
                            'journal_id': payslip_run.journal_id.id,
                            'period_id': period_id.id,
                            'debit': rubricas[rubrica].total,
                            'credit': 0.0,
                            'payslip_run_id': payslip_run.id,
                        })
                        line_ids.append(debit_line)
                        debit_sum += \
                            debit_line[2]['debit'] - debit_line[2][
                                'credit']
                if float_compare(
                        credit_sum, debit_sum, precision_digits=precision
                ) == -1:
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'date': timenow,
                        'partner_id': False,
                        'account_id': conta_credito.id,
                        'journal_id': payslip_run.journal_id.id,
                        'period_id': period_id.id,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                        'payslip_run_id': payslip_run.id,
                    })
                    line_ids.append(adjust_credit)
                elif float_compare(
                        debit_sum, credit_sum, precision_digits=precision
                ) == -1:
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'date': timenow,
                        'partner_id': False,
                        'account_id': conta_debito.id,
                        'journal_id': payslip_run.journal_id.id,
                        'period_id': period_id.id,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                        'payslip_run_id': payslip_run.id
                    })
                    line_ids.append(adjust_debit)
                if not payslip_run.move_id:
                    move.update({'line_id': line_ids})
                    move_id = move_obj.create(move)
                else:
                    for line in line_ids:
                        line[2].update({'move_id': payslip_run.move_id.id})
                        self.env['account.move.line'].create(line[2])
                    move_id = payslip_run.move_id
                self.write({'move_id': move_id.id})
                if payslip_run.journal_id.entry_posted:
                    move_obj.post(move_id)
#             else:
#                raise exceptions.Warning(
#                    "Não foi selecionada nenhuma conta de crédito ou "
#                    "débito para o lote de holerites!"
#                )
        else:
            raise exceptions.Warning(
                ("Erro!"),
                ("É preciso selecionar um diário para realizar "
                 "a contabilização!")
            )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(L10nBrHrPayslip, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu
        )
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res
