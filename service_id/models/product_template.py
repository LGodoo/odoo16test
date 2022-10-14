# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    
    modem_display = fields.Boolean('Display Modem', default=False)
    static_ip_display = fields.Boolean('Display Static IP', default=False)
    portability_number_display = fields.Boolean('Portability Number', default=False)


