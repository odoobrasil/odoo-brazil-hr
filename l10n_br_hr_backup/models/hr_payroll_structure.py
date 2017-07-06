# -*- coding: utf-8 -*-
# Copyright (C) 2017 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.multi
    def _compute_xml_rubrica(self):
        """
        Função que gera XML da estrutura atual
        """

        for regra in self:

            # Se a regra ja tiver identificação no ir_model_data exibe a
            # external_id, senão exibe a external id que sera criada pelo
            # modulo de backup
            backup = self.env['hr.backup']

            id = backup.get_external_id(
                regra, 'hr_payroll_structure_%s' % regra.code)

            record = \
                "\t\t<record id=\"%s\" model=\"hr.payroll.structure\"> \n" % id

            record += backup.get_text_field(regra.code, 'code')
            record += backup.get_text_field(regra.name, 'name')
            record += backup.get_text_field(regra.note, 'note')
            record += backup.get_many_to_many(regra.rule_ids, 'rule_ids')
            record += backup.get_text_field(regra.tipo_saque, 'tipo_saque')
            record += backup.get_many_to_one_field(
                regra.ferias, 'ferias', criar_model_data=True)
            record += backup.get_many_to_one_field(
                regra.parent_id, 'parent_id', criar_model_data=True)
            record += backup.get_many_to_many(
                regra.children_ids, 'children_ids')
            record += backup.get_many_to_one_field(
                regra.company_id, 'company_id')
            record += backup.get_text_field(
                regra.tipo_afastamento_cef, 'tipo_afastamento_cef')
            record += backup.get_text_field(
                regra.tipo_afastamento_sefip, 'tipo_afastamento_sefip')
            record += backup.get_text_field(
                regra.tipo_estrutura, 'tipo_estrutura')
            record += backup.get_text_field(
                regra.tipo_desligamento_rais, 'tipo_desligamento_rais')

            record += "\t\t</record>\n\n"

            regra.generate_xml = record

    generate_xml = fields.Text(
        string='XML da rubrica gerado automaticamente',
        compute='_compute_xml_rubrica',
        help='Cole esse xml em seu modulo',
    )

    last_backup = fields.Datetime(
        string='Data do ultimo backup',
    )
