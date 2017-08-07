# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    payslip_id = fields.Many2one(
        comodel_name="hr.payslip",
        string="Payslip",
    )

    payslip_run_id = fields.Many2one(
        comodel_name="hr.payslip.run",
        string="Payslip Run",
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payslip_id = fields.Many2one(
        comodel_name="hr.payslip",
        string="Payslip",
    )

    payslip_run_id = fields.Many2one(
        comodel_name="hr.payslip.run",
        string="Payslip Run",
    )
