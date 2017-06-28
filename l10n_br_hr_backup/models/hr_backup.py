# -*- coding: utf-8 -*-
# Copyright (C) 2017 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
import re

from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class HrBackup(models.Model):
    _name = 'hr.backup'

    @api.multi
    def get_many_to_one_field(self, field_val, field_name,
                              criar_model_data=False):
        """
        Função para retornar campo e valor no formato XML.
        """
        # if isinstance(field_val, )

        if field_val:
            if field_val._get_external_ids().get(field_val.id):
                field_val = field_val._get_external_ids().get(field_val.id)[0]

            elif criar_model_data:
                self.registrar_modelo_ir_model_data(field_val)
                _logger.info('Criado ir_model_data do Objeto relacional %s '
                             'do modelo %s - %s' %
                             (field_name, field_val._name, field_val.name))

            else:
                _logger.info(
                    "Informacao do campo %s no modelo %s nao foi salva."
                    "Campo relacional %s nao possui XML." %
                    (field_name, field_val._name, field_val.name))

        linha = "\t\t\t<field name=\"%s\" ref=\"%s\"/>\n" % \
                (field_name, field_val or '')
        return linha

    @api.multi
    def get_text_field(self, field_val, field_name):
        """
        Função para retornar campo e valor no formato XML.
        """
        linha = "\t\t\t<field name=\"%s\">%s</field>\n" % \
                (field_name, field_val or '')
        return linha

    @api.multi
    def get_many_to_many(self, field_vals, field_name):
        """
        Função para retornar campo e valor no formato XML.
        """
        refs = ''
        for field in field_vals:
            if field and field._get_external_ids().get(field.id):
                refs += "ref('%s'), " % \
                        field._get_external_ids().get(field.id)[0]
        line = \
            "\t\t\t<field name=\"%s\" eval=\"[(6, 0, [%s])]\" />\n" %\
            (field_name, refs[:-2])

        return line

    @api.multi
    def formata_caracteres_xml(self, field):
        """
        Formata o XML que nao pode conter caracateres como '<=' ou '>='
        """
        # Validar a entrada de dados
        if not isinstance(field, (str, unicode)):
            return field

        # Menor igual
        field = re.sub('<=', ' &lt;= ', field)
        # Menor
        field = re.sub('<', ' &lt; ', field)
        # Maior Igual
        field = re.sub('>=', ' &gt;= ', field)
        # Maior
        field = re.sub('>', ' &gt; ', field)

        return field

    @api.multi
    def get_external_id(self, object, name):
        """
        Retorna a referencia externa se existir senao retorna o nome
        passado como parametro
        :param object: instancia do objeto
        :param name:   str - nome do record ex.: hr_salary_rule_RUBRICA01
        """
        if object._get_external_ids().get(object.id):
            return object._get_external_ids().get(object.id)[0]
        return name

    @api.multi
    def registrar_modelo_ir_model_data(self, objeto, name=False):
        """
        Função que registra na tabela ir_model_data a existencia do objeto que
        foi criado via interface
        :param objeto: Objeto a ser registrado
        :param name: nome do objeto a ser registrado na tabela,
        :return: instancia do ir_model_data
        """
        ir_model_data_obj = self.env['ir.model.data']

        # Se nao passar nenhum nome no parametro, utilizar o nome do objeto
        if not name:
            name = objeto._name

        vals = {
            'name': name,
            'module': 'l10n_br_hr_payroll',
            'model': objeto._model,
            'res_id': objeto.id,
        }

        return ir_model_data_obj.create(vals)

    @api.multi
    def escrever_arquivo_backup(self, name, texto):

        template_path = '{}/../data/' + name + '.xml'
        template_path = template_path.format(os.path.dirname(__file__))

        xml_antigo = open(template_path, 'r')
        xml_antigo = xml_antigo.read()

        if xml_antigo:
            # Remover as TAGS de fechamento do arquivo
            xml_antigo = re.sub(r'\<\/data>', '', xml_antigo)
            xml_antigo = re.sub(r'\<\/openerp>', '', xml_antigo)
        else:
            xml_antigo = '\t<openerp>\n\t\t<data>\n'

        xml_final = xml_antigo + '\t\t<!-- BACKUP EM  '
        xml_final += str(fields.datetime.now()) + ' -->\n'
        xml_final += texto
        xml_final += '\t\t</data>\n\t</openerp>\n'

        backup_xml = open(template_path, 'w')
        backup_xml.write(xml_final)
        backup_xml.close()

    @api.multi
    def gerar_backup_objetos_criados(self, modelo):
        """
        Função que busca as regras que foram criadas somente pela interface,
        dispara uma função para registro na tabela ir_model_data e retorna um
        texto em xml para gerar o backup das regras
        """
        model_obj = self.env[modelo]
        ir_model_data_obj = self.env['ir.model.data']

        # Buscar todas as regras que foram geradas apartir do XML
        res_id = ir_model_data_obj.search([
            ('model', '=', modelo),
        ]).mapped('res_id')

        # Identificar regras geradas pela interface, que nao tem XML
        regras_sem_xml = model_obj.search([
            ('id', 'not in', res_id),
        ])

        # variavel que contem as regras em xml
        models_xml = u''

        for model_sem_xml in regras_sem_xml:
            # Se nao achar um id externo cria na tabela ir_model_data
            if not self.get_external_id(model_sem_xml, False):
                model_label = model_sem_xml.code \
                    if model_sem_xml.code else str(model_sem_xml.id)
                name = modelo.replace('.', '_') + '_' + model_label
                self.registrar_modelo_ir_model_data(model_sem_xml, name)
                models_xml += model_sem_xml.generate_xml

        return models_xml.encode('utf-8'), len(regras_sem_xml)

    @api.multi
    def gerar_backup_objetos_editados(self, modelo):
        """
        Função que gera um texto no formato xml para realizar o backup
        """
        model_obj = self.env[modelo]
        models = model_obj.search([])

        models_xml = u''
        models_qty = 0
        for model in models:
            if model.create_date != model.write_date:
                if (not model.last_backup) or \
                        (model.write_date > model.last_backup):
                    models_xml += model.generate_xml
                    models_qty += 1
                    model.last_backup = fields.datetime.now()
        return models_xml.encode('utf-8'), models_qty

    @api.multi
    def atualizar_modelos_ja_exportados(self, model):
        """
        Os modelos exportadas anteriormente, ja possuem registro no
        ir_model_data, mas o registro aponta para um modulo inválido (export)
        A função readequara esses registros apontando para o modulo de backup
        :return:
        """
        model_obj = self.env[model]
        ir_model_data_obj = self.env['ir.model.data']

        modelos_ja_exportados = ir_model_data_obj.search([
            ('model', '=', model),
            ('module', '=', '__export__'),
        ])

        for modelo_ja_exportado in modelos_ja_exportados:
            modelo_id = model_obj.browse(modelo_ja_exportado.res_id)
            name = model.replace('.', '_') + '_' + modelo_id.code \
                if modelo_id.code else str(modelo_id.id)
            modelo_ja_exportado.module = 'l10n_br_hr_payroll'
            modelo_ja_exportado.name = name
            modelo_id.write_date = fields.datetime.now()

    @api.multi
    def gerar_backup(self):
        """
        Rotina chamada pela interface para fazer backup dos objetos de RH
         editados e criados via interface
        """
        models = [
            'hr.salary.rule.category',
            'hr.salary.rule',
            'hr.payroll.structure',
        ]

        for model in models:
            # Verificar Modelos ja exportados anteriormente
            self.atualizar_modelos_ja_exportados(model)

            # Gerar xml com todas os objetos criados via interface
            xml_objetos_criadas, qty_objetos_criadas = \
                self.gerar_backup_objetos_criados(model)

            # Gerar xml com todos os objetos editados via interface
            xml_objetos_editadas, qty_objetos_editados = \
                self.gerar_backup_objetos_editados(model)

            # Ajustar estrutura do xml
            xml_objetos = '\n\t\t<!-- Objetos Criados: %d --> \n\n' % \
                          qty_objetos_criadas

            xml_objetos += xml_objetos_criadas

            xml_objetos += '\n\t\t<!-- Objetos Editadas: %d --> \n\n' % \
                           qty_objetos_editados

            xml_objetos += xml_objetos_editadas

            # Escreve no arquivo XML do modulo
            self.escrever_arquivo_backup(model.replace('.', '_'), xml_objetos)
