from openerp import api, fields, models


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    ano = fields.Integer(
        string=u'Ano referencia',
    )

    contrato_id = fields.Many2one(
        comodel_name='hr.contract',
        string=u'Contrato associado',
        required=True,
    )

    @api.onchange('contrato_id')
    def onchange_contrato(self):
        for holiday in self:
            holiday.employee_id = holiday.contrato_id.employee_id
