# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from ..constantes_rh import (MESES, MODALIDADE_ARQUIVO, CODIGO_RECOLHIMENTO,
                             RECOLHIMENTO_GPS, RECOLHIMENTO_FGTS,
                             CENTRALIZADORA, SEFIP_CATEGORIA_TRABALHADOR)
import logging
import re

from .arquivo_sefip import SEFIP

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import tira_acentos
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')

SEFIP_STATE = [
    ('rascunho', u'Rascunho'),
    ('confirmado', u'Confirmada'),
    ('enviado', u'Enviado'),
]


class L10nBrSefip(models.Model):
    _name = 'l10n_br.hr.sefip'

    state = fields.Selection(selection=SEFIP_STATE, default='rascunho')
    # responsible_company_id = fields.Many2one(
    #     comodel_name='res.company', string=u'Empresa Responsável'
    # )
    responsible_user_id = fields.Many2one(
        comodel_name='res.partner', string=u'Usuário Responsável'
    )
    company_id = fields.Many2one(comodel_name='res.company', string=u'Empresa')
    mes = fields.Selection(selection=MESES, string=u'Mês')
    ano = fields.Char(string=u'Ano')
    modalidade_arquivo = fields.Selection(
        selection=MODALIDADE_ARQUIVO, string=u'Modalidade do arquivo'
    )
    codigo_recolhimento = fields.Selection(
        string=u'Código de recolhimento', selection=CODIGO_RECOLHIMENTO
    )
    recolhimento_fgts = fields.Selection(
        string=u'Recolhimento do FGTS', selection=RECOLHIMENTO_FGTS
     )
    data_recolhimento_fgts = fields.Date(
        string=u'Data de recolhimento do FGTS'
    )
    codigo_recolhimento_gps = fields.Char(
        string=u'Código de recolhimento do GPS'
    )
    recolhimento_gps = fields.Selection(
        string=u'Recolhimento do GPS', selection=RECOLHIMENTO_GPS
    )
    data_recolhimento_gps = fields.Date(
        string=u'Data de recolhimento do GPS'
    )
    codigo_fpas = fields.Char(string=u'Código FPAS', default='736')
    codigo_outras_entidades = fields.Char(string=u'Código de outras entidades')
    centralizadora = fields.Selection(
        selection=CENTRALIZADORA, string=u'Centralizadora',
        default='1'
    )
    data_geracao = fields.Date(string=u'Data do arquivo')
    #Processo ou convenção coletiva
    num_processo = fields.Char(string=u'Número do processo')
    ano_processo = fields.Char(string=u'Ano do processo')
    vara_jcj = fields.Char(string=u'Vara/JCJ')
    data_inicio = fields.Date(string=u'Data de Início')
    data_termino = fields.Date(string=u'Data de término')
    sefip = fields.Text(
        string=u'Prévia do SEFIP'
    )

    def _validar(self, word, tam, tipo='AN'):
        """
        Função Genérica utilizada para validação de campos que são gerados
        nos arquivos TXT's
        :param tipo: str - Tipo de palavras validadas:
            -   A -> Alfabéticas -> Apenas letras do alfabeto
            -   D -> Data -> Apenas numeral
            -   V -> Valor -> Valores decimais, retirando a virgula
            -   N -> Numerico -> Apenas numeros preechidos com zero a esq.
            -   AN -> Alfanumericos -> Aceita numeros e caracateres sem acentos
        :param word: str - palavra a ser validada
        :param tam: int - Tamanho que a palavra deve ser
        :return: str - Palavra formatada de acordo com tipo e tamanho
        """
        if not word:
            word = u''

        if tipo == 'A':         # Alfabetico
            word = tira_acentos(word)
            # tirar tudo que nao for letra do alfabeto
            word = re.sub('[^a-zA-Z]', ' ', word)
            # Retirar 2 espaços seguidos
            word = re.sub('[ ]+', ' ', word)
            word = word.upper()
            return unicode.ljust(unicode(word), tam)[:tam]

        elif tipo == 'D':       # Data
            # Retira tudo que nao for numeral
            word = data.formata_data(word)
            word = re.sub(u'[^0-9]', '', str(word))
            return unicode.ljust(unicode(word), tam)[:tam]

        elif tipo == 'V':       # Valor
            # Pega a parte decimal como inteiro e nas duas ultimas casas
            word = int(word * 100) if word else 0
            # Preenche com zeros a esquerda
            word = str(word).zfill(tam)
            return word[:tam]

        elif tipo == 'N':       # Numerico
            # Preenche com zeros a esquerda
            word = re.sub('[^0-9]', '', str(word))
            word = str(word).zfill(tam)
            return word[:tam]

        elif tipo == 'AN':      # Alfanumerico
            word = word.upper()
            # Tira acentos da palavras
            word = tira_acentos(word)
            # Preenche com espaço vazio a esquerda
            return unicode.ljust(unicode(word), tam)[:tam]
        else:
            return word

    # @api.depends('responsible_user_id', 'company_id', 'mes', 'ano',
    #              'modalidade_arquivo', 'codigo_recolhimento', 'codigo_fpas',
    #              'recolhimento_fgts', 'data_recolhimento_fgts', 'vara_jcj',
    #              'codigo_recolhimento_gps', 'recolhimento_gps', 'data_inicio',
    #              'data_recolhimento_gps', 'codigo_outras_entidades',
    #              'centralizadora', 'data_geracao', 'num_processo',
    #              'ano_processo', 'data_termino'
    #              )
    @api.multi
    def gerar_sefip(self):
        sefip = SEFIP()
        self._preencher_registro_00(sefip)
        # self._preencher_registro_10(sefip)
        for folha in self.env['hr.payslip'].search([
            ('mes_do_ano', '=', self.mes),
            ('ano', '=', self.ano)
        ]).sorted(key=lambda folha: folha.employee_id.pis_pasep):
            self._preencher_registro_30(sefip, folha)
        self.sefip = sefip._gerar_arquivo_SEFIP()

    # def _registro_00(self):
    #     _validar = self._validar
    #     sefip = '00'                        # Tipo de Registro
    #     sefip += _validar('', 51, 'AN')     # Brancos
    #     sefip += _validar('1', 1, 'N')      # Tipo de Remessa
    #     sefip += '1' if self.responsible_user_id.is_company \
    #         else '3'                        # Tipo de Inscrição - Responsável
    #     sefip += _validar(
    #         self.responsible_user_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição do Responsável
    #     sefip += _validar(
    #         self.responsible_user_id.legal_name, 30, 'AN'
    #     )                                   # Razão Social
    #     sefip += _validar(
    #         self.responsible_user_id.name, 20, 'A'
    #     )                                   # Nome Pessoa Contato
    #     logradouro = _validar(self.responsible_user_id.street, 0, '') + ' '
    #     logradouro += _validar(self.responsible_user_id.number, 0, '') + ' '
    #     logradouro += _validar(self.responsible_user_id.street2, 0, '')
    #     sefip += _validar(
    #         logradouro, 50, 'AN'
    #     )                                   # Logradouro
    #     sefip += _validar(
    #         self.responsible_user_id.district, 20, 'AN'
    #     )                                   # Bairro
    #     sefip += _validar(
    #         self.responsible_user_id.zip, 8, 'N'
    #     )                                   # CEP
    #     sefip += _validar(
    #         self.responsible_user_id.l10n_br_city_id, 20, 'AN'
    #     )                                   # Cidade
    #     sefip += _validar(
    #         self.responsible_user_id.state_id.code, 2, 'N'
    #     )                                   # UF
    #     sefip += _validar(
    #         self.responsible_user_id.phone, 12, 'N'
    #     )                                   # Telefone
    #     sefip += _validar(
    #         self.responsible_user_id.website, 60, 'AN'
    #     )                                   # Site
    #     sefip += _validar(self.ano, 4, 'N') + \
    #         _validar(self.mes, 2, 'N')      # Competência
    #     sefip += _validar(
    #         self.codigo_recolhimento, 3, 'N'
    #     )                                   # Código de Recolhimento
    #     sefip += _validar(
    #         self.recolhimento_fgts, 1, 'N'
    #     )                                   # Recolhimento FGTS
    #     sefip += _validar(
    #         self.modalidade_arquivo, 1, 'N'
    #     )                                   # Modalidade do Arquivo
    #     sefip += _validar(
    #         fields.Datetime.from_string(
    #             self.data_recolhimento_fgts).strftime('%d%m%Y'), 8, 'D'
    #     )                                   # Data de Recolhimento do FGTS
    #     sefip += _validar(
    #         self.recolhimento_gps, 1, 'N'
    #     )                                   # Indicador de Recolhimento PS
    #     sefip += _validar(
    #         fields.Datetime.from_string(
    #             self.data_recolhimento_gps).strftime('%d%m%Y'), 8, 'D'
    #     )                                   # Data de Recolhimento PS
    #     sefip += _validar(
    #         '', 7, 'N'
    #     )                                   # Índice de Recolhimento em Atraso
    #     sefip += '1' if self.company_id.supplier_partner_id.is_company \
    #         else '3'                    # Tipo de Inscrição do Fornecedor
    #     sefip += _validar(
    #         self.company_id.supplier_partner_id.cnpj_cpf, 14, 'N'
    #     )                               # Inscrição do Fornecedor
    #     sefip += _validar('', 18, 'AN')
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip

    def _preencher_registro_00(self, sefip):
        sefip.tipo_inscr_resp = '1' if self.responsible_user_id.is_company \
            else '3'
        sefip.inscr_resp = self.responsible_user_id.cnpj_cpf
        sefip.nome_resp = self.responsible_user_id.parent_id.name
        sefip.nome_contato = self.responsible_user_id.name
        sefip.arq_logradouro = self.responsible_user_id.street or '' + ' ' + \
                               self.responsible_user_id.number or ''+ ' ' + \
                               self.responsible_user_id.street2 or ''
        sefip.arq_bairro = self.responsible_user_id.district
        sefip.arq_cep = self.responsible_user_id.zip
        sefip.arq_cidade = self.responsible_user_id.l10n_br_city_id.name
        sefip.arq_uf = self.responsible_user_id.state_id.code
        sefip.tel_contato = self.responsible_user_id.phone
        sefip.internet_contato = self.responsible_user_id.website
        sefip.competencia = self.ano + self.mes
        sefip.cod_recolhimento = self.codigo_recolhimento
        sefip.indic_recolhimento_fgts = self.recolhimento_fgts
        sefip.modalidade_arq = self.modalidade_arquivo
        sefip.data_recolhimento_fgts = fields.Datetime.from_string(
                self.data_recolhimento_fgts).strftime('%d%m%Y')
        sefip.indic_recolh_ps = self.recolhimento_gps
        sefip.data_recolh_ps = fields.Datetime.from_string(
                self.data_recolhimento_gps).strftime('%d%m%Y')
        sefip.tipo_inscr_fornec = (
            '1' if self.company_id.supplier_partner_id.is_company else '3')
        sefip.inscr_fornec = self.company_id.supplier_partner_id.cnpj_cpf
        return sefip._registro_00_informacoes_responsavel()

    # def _registro_10(self):
    #     _validar = self._validar
    #     sefip = '10'                        # Tipo de Registro
    #     sefip += '1'                        # Tipo de Inscrição - Empresa
    #     sefip += _validar(
    #         self.company_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição do Empresa
    #     sefip += '0'*36                     # Zeros
    #     sefip += _validar(
    #         self.company_id.legal_name, 40, 'AN'
    #     )                                   # Razão Social
    #     logradouro = _validar(self.company_id.street, 0, '') + ' '
    #     logradouro += _validar(self.company_id.number, 0, '') + ' '
    #     logradouro += _validar(self.company_id.street2, 0, '')
    #     sefip += _validar(
    #         logradouro, 50, 'AN'
    #     )                                   # Logradouro
    #     sefip += _validar(
    #         self.company_id.district, 20, 'AN'
    #     )                                   # Bairro
    #     sefip += _validar(
    #         self.company_id.zip, 8, 'N'
    #     )                                   # CEP
    #     sefip += _validar(
    #         self.company_id.l10n_br_city_id, 20, 'AN'
    #     )                                   # Cidade
    #     sefip += _validar(
    #         self.company_id.state_id.code, 2, 'N'
    #     )                                   # UF
    #     sefip += _validar(
    #         self.company_id.phone, 12, 'N'
    #     )                                   # Telefone
    #     sefip += 'N'                        # Indicador Alteração Endereço
    #     sefip += _validar(
    #         self.company_id.cnae, 7, 'N'
    #     )                                   # CNAE
    #     sefip += 'N'                        # Indicação de Alteração do CNAE
    #     sefip += _validar(self.env['l10n_br.hr.rat.fap'].search([
    #         ('year', '=', self.ano)], limit=1
    #     ).rat_rate, 2, 'V') or '00'         # Alíquota RAT
    #     sefip += self.centralizadora        # Código de Centralização
    #     sefip += '1'                        # SIMPLES
    #     sefip += self.codigo_fpas           # FPAS
    #     sefip += '0003'                     # Código de Outras Entidades
    #     sefip += '2100'                     # Código de Pagamento GPS
    #     sefip += '     '                    # Percentual de Isenção Filantropia
    #     sefip += _validar('', 15, 'N')      # Salário-família
    #     sefip += _validar('', 15, 'N')      # Salário-maternidade
    #     sefip += '0'*15                     # Contrib. Desc. Empregado
    #     sefip += '0'                        # Indicador de positivo ou negativo
    #     sefip += '0'*14                     # Valor devido à previdência social
    #     sefip += ' '*16                     # Banco
    #     sefip += '0'*45                     # Zeros
    #     sefip += ' '*4                      # Brancos
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip

    def _preencher_registro_10(self, sefip):
        aliquota_rat = self.env['l10n_hr.rat.fap'].search(
            [('year', '=', self.ano)], limit=1).rat_rate or '0'
        # sefip.tipo_inscr_empresa = self.
        sefip.inscr_empresa = self.company_id.cnpj_cei
        sefip.emp_nome_razao_social = self.company_id.name
        sefip.emp_logradouro = self.company_id.street or '' + ' ' + \
                               self.company_id.number or '' + ' ' + \
                               self.company_id.street2 or ''
        sefip.emp_bairro = self.company_id.district
        sefip.emp_cep = self.company_id.zip
        sefip.emp_cidade = self.company_id.l10n_br_city.name
        sefip.emp_uf = self.company_id.state_id.code
        sefip.emp_tel = self.company_id.phone
        # sefip.emp_indic_alteracao_endereco = 'n'
        sefip.emp_cnae = self.company_id.cnae
        # sefip.emp_indic_alteracao_cnae = 'n'
        sefip.emp_aliquota_RAT = aliquota_rat
        sefip.emp_cod_centralizacao = self.centralizadora
        sefip.emp_simples = '1' if self.company_id.fiscal_type == '3' else '2'
        sefip.emp_FPAS = self.codigo_fpas
        sefip.emp_cod_outras_entidades = self.codigo_outras_entidades
        sefip.emp_cod_pagamento_GPS = self.codigo_recolhimento_gps
        # sefip.emp_percent_isencao_filantropia = self.
        # sefip.emp_salario_familia =
        # sefip.emp_salario_maternidade =
        # sefip.emp_banco = self.company_id.bank_id[0].bank
        # sefip.emp_ag = self.company_id.bank_id[0].agency
        # sefip.emp_cc = self.company_id.bank_id[0].account
        return sefip._registro_10_informacoes_empresa()


    # def _registro_30(self, folha):
    #     _validar = self._validar
    #     sefip = '30'                        # Tipo de Registro
    #     sefip += '1'                        # Tipo de Inscrição - Empresa
    #     sefip += _validar(
    #         self.company_id.cnpj_cpf, 14, 'N'
    #     )                                   # Inscrição Empresa
    #     sefip += ' '                        # Tipo Inscrição Tomador/Obra
    #     sefip += ' '*14                     # Inscrição Tomador/Obra
    #     sefip += _validar(
    #         folha.employee_id.pis_pasep, 11, 'N'
    #     )                                   # PIS/PASEP
    #     sefip += _validar(
    #         folha.contract_id.date_start, 8, 'D'
    #     )                                   # Data de Admissão
    #     sefip += '01'                       # Categoria Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.name, 70, 'A'
    #     )                                   # Nome Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.registration, 11, 'N'
    #     )                                   # Matrícula Trabalhador
    #     sefip += _validar(
    #         folha.employee_id.ctps, 7, 'N'
    #     )                                   # Número CTPS
    #     sefip += _validar(
    #         folha.employee_id.ctps_series, 5, 'N'
    #     )                                   # Série CTPS
    #     sefip += _validar(
    #         folha.contract_id.date_start
    #     )                                   # Data Opção FGTS
    #     sefip += _validar(
    #         folha.employee_id.birthday, 8, 'D'
    #     )                                   # Data de Nascimento
    #     sefip += _validar(
    #         folha.contract_id.job_id.cbo_id.code, 5, 'N'
    #     )                                   # CBO
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Remuneração sem 13º
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Remuneração 13º
    #     sefip += _validar(
    #         '', 2, 'AN'
    #     )                                   # Classe de Contribuição (errado)
    #     sefip += _validar(
    #         '', 2, 'AN'
    #     )                                   # Ocorrência
    #     sefip += _validar(
    #         '', 15, 'N'
    #     )                                   # Valor descontado do segurado ocorrencia 05
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo Contr. Prev. (errado)
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo 13º - 1 (errado)
    #     sefip += _validar(
    #         folha.contract_id.wage, 15, 'N'
    #     )                                   # Base de Cálculo 13º - 2 (errado)
    #     sefip += _validar(
    #         '', 98, 'AN'
    #     )                                   # Brancos
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip


    def _preencher_registro_30(self, sefip, folha):
        sefip.tipo_inscr_empresa = '1'
        sefip.inscr_empresa = self.company_id.cnpj_cpf
        sefip.tipo_inscr_tomador = ' '
        sefip.inscr_tomador = ' '*14
        sefip.pis_pasep_ci = folha.employee_id.pis_pasep
        sefip.data_admissao = folha.contract_id.date_start
        sefip.categoria_trabalhador = SEFIP_CATEGORIA_TRABALHADOR.get(
            folha.contract_id.categoria, '01')
        sefip.nome_trabalhador = folha.employee_id.name
        sefip.matricula_trabalhador = folha.employee_id.registration
        sefip.num_ctps = folha.employee_id.ctps
        sefip.serie_ctps = folha.employee_id.ctps_series
        # sefip.data_de_opcao =
        sefip.data_de_nascimento = folha.employee_id.birthday
        sefip.trabalhador_cbo = folha.job_id.cbo_id.code
        # sefip.trabalhador_remun_sem_13 = holerite.salario-total
        # sefip.trabalhador_remun_13 =
        # sefip.trabalhador_classe_contrib =
        # ONDE SE ENCONTRAM INFORMAÇÕES REFERENTES A INSALUBRIDADE, DEVERIAM ESTAR NO CAMPO job_id?
        #sefip.trabalhador_ocorrencia =
        # sefip.trabalhador_valor_desc_segurado =
        sefip.trabalhador_remun_base_calc_contribuicao_previdenciaria = folha.wage
        # sefip.trabalhador_base_calc_13_previdencia_competencia =
        # sefip.trabalhador_base_calc_13_previdencia_GPS =

    # def _preencher_registro_90(self):
    #     sefip = '90'
    #     sefip += '9'*51
    #     sefip += ' '*306
    #     sefip += '*'
    #     sefip += '\n'
    #     return sefip
