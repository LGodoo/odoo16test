from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.tools.sql import column_exists, create_column


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    service_id_invoice = fields.Many2one(
    'sale.service.details', string='Service ID')