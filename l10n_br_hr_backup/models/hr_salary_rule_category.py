# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import unicode_literals, division, print_function

from openerp import api, fields, models


class HrSalaryRuleCategory(models.Model):
    _inherit = b'hr.salary.rule.category'

    @api.multi
    def _compute_xml_rubrica(self):
        """
        Função que gera XML da rubrica atual
        """

        for categoria in self:

            # Se a regra ja tiver identificação no ir_model_data exibe a
            # external_id, senão exibe a external id que sera criada pelo
            # modulo de backup
            backup = self.env['hr.backup']

            id = backup.get_external_id(
                categoria, 'hr_salary_rule_category_%s' % categoria.code)

            record = \
                "\t\t<record id=\"%s\" " \
                "model=\"hr.salary.rule.category\"> \n" % id
            record += backup.get_text_field(categoria.name, 'name')
            record += backup.get_text_field(categoria.code, 'code')
            record += backup.get_many_to_one_field(
                categoria.company_id, 'company_id')
            record += backup.get_text_field(categoria.note, 'note')
            record += backup.get_many_to_one_field(
                categoria.parent_id, 'parent_id', criar_model_data=True)
            record += "\t\t</record>\n\n"
            categoria.generate_xml = record

    generate_xml = fields.Text(
        string='XML da rubrica gerado automaticamente',
        compute='_compute_xml_rubrica',
        help='Cole esse xml em seu módulo',
    )

    last_backup = fields.Datetime(
        string='Data do ultimo backup',
    )
