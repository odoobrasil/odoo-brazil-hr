# -*- coding: utf-8 -*-
# Copyright (C) 2017 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import unicode_literals, division, print_function

from openerp import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = b'hr.salary.rule'

    @api.multi
    def _compute_xml_rubrica(self):
        """
        Função que gera XML da rubrica atual
        """

        for regra in self:

            # Se a regra ja tiver identificação no ir_model_data exibe a
            # external_id, senão exibe a external id que sera criada pelo
            # modulo de backup
            backup = self.env['hr.backup']

            id = backup.get_external_id(
                regra, 'hr_salary_rule_%s' % regra.code)

            record = \
                "\t\t<record id=\"%s\" model=\"hr.salary.rule\"> \n" % id

            record += backup.get_text_field(regra.code, 'code')
            record += backup.get_text_field(regra.name, 'name')
            record += backup.get_text_field(regra.active, 'active')
            record += backup.get_text_field(regra.sequence, 'sequence')

            record += backup.get_many_to_one_field(
                regra.category_id, 'category_id')
            record += backup.get_text_field(
                regra.condition_select, 'condition_select')

            condition = backup.formata_caracteres_xml(regra.condition_python)
            record += backup.get_text_field(condition, 'condition_python')
            amount = backup.formata_caracteres_xml(regra.amount_python_compute)
            record += backup.get_text_field(amount, 'amount_python_compute')

            custom_amount = backup.formata_caracteres_xml(
                regra.custom_amount_python_compute)
            record += backup.get_text_field(
                custom_amount, 'custom_amount_python_compute')

            record += backup.get_text_field(
                regra.amount_select, 'amount_select')
            record += backup.get_text_field(
                regra.custom_amount_select, 'custom_amount_select')
            record += backup.get_text_field(
                regra.compoe_base_INSS, 'compoe_base_INSS')
            record += backup.get_text_field(
                regra.compoe_base_IR, 'compoe_base_IR')
            record += backup.get_text_field(
                regra.compoe_base_FGTS, 'compoe_base_FGTS')
            record += backup.get_text_field(
                regra.amount_fix, 'amount_fix')
            record += backup.get_text_field(
                regra.custom_amount_fix, 'custom_amount_fix')
            record += backup.get_text_field(
                regra.amount_percentage, 'amount_percentage')
            record += backup.get_text_field(
                regra.amount_percentage_base, 'amount_percentage_base')
            record += backup.get_text_field(
                regra.custom_amount_percentage_base,
                'custom_amount_percentage_base')
            record += backup.get_text_field(
                regra.custom_amount_percentage, 'custom_amount_percentage')
            record += backup.get_text_field(
                regra.appears_on_payslip, 'appears_on_payslip')
            record += backup.get_text_field(
                regra.condition_range, 'condition_range')
            record += backup.get_text_field(
                regra.condition_range_min, 'condition_range_min')
            record += backup.get_text_field(
                regra.condition_range_max, 'condition_range_max')
            record += backup.get_text_field(regra.note, 'note')
            record += backup.get_text_field(
                regra.calculo_nao_padrao, 'calculo_nao_padrao')
            record += backup.get_text_field(regra.quantity, 'quantity')
            record += backup.get_text_field(
                regra.custom_quantity, 'custom_quantity')
            record += backup.get_text_field(regra.tipo_media, 'tipo_media')

            record += backup.get_many_to_one_field(
                regra.parent_rule_id, 'parent_rule_id', criar_model_data=True)
            record += backup.get_many_to_one_field(
                regra.company_id, 'company_id')
            record += backup.get_many_to_one_field(
                regra.register_id, 'register_id')

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
