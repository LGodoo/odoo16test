# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import traceback

from ast import literal_eval
from collections import Counter
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from uuid import uuid4

from odoo import api, fields, models, Command, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date, is_html_empty, config
from odoo.tools.float_utils import float_is_zero


_logger = logging.getLogger(__name__)

class SaleServiceDetails(models.Model):
    _name = "sale.service.details"
    _description = "Service ID"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    #_inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin', 'utm.mixin']
    #_check_company_auto = True
    #_mail_post_access = 'read'
    
    name = fields.Char(required=True, tracking=True, index=True, copy=False)
    ip_address = fields.Char(required=False, tracking=True, index=True, copy=False, string='IP Address')
    modem = fields.Char(required=False, tracking=True, index=True, copy=False, string='Modem')
    portability_number = fields.Char(required=False, tracking=True, index=True, copy=False, string='Portability Number')

    
    
    recurring_invoice_line_ids = fields.One2many('sale.subscription.line', 'service_id', string='Subscription Lines')
    subscription_id = fields.Many2one('sale.subscription', related='recurring_invoice_line_ids.analytic_account_id', tracking=True, index=True, readonly=True)
    product = fields.Many2one('product.product', related='recurring_invoice_line_ids.product_id', tracking=True, index=True, string='Product', readonly=True)
    product_category = fields.Many2one('product.category', related='product.categ_id', tracking=True, index=True, string='Product', readonly=True)

    modem_display = fields.Boolean('Modem Display', related='product.modem_display', readonly=True)
    static_ip_display = fields.Boolean('Modem Display', related='product.static_ip_display', readonly=True)

    
    provider_name = fields.Many2one('res.partner', tracking=True, string='Provider')
    portability_number_display = fields.Boolean('Portability Number Display', related='product.portability_number_display', readonly=True)

    @api.constrains('name')
    def _check_name_unique(self):

        self.flush(['name'])

        name_check = self.env['sale.service.details'].search([('name', '=', self.name)])
        _logger.error('Found service ids: %s %s', len(name_check), name_check)

        if len(name_check) > 1:
            raise ValidationError(_('Douplicate Service ID: %s - Subscription: %s', name_check[0].name, name_check[0].subscription_id.display_name))

            
    @api.onchange('portability_number')
    def update_port_number_on_sub_line(self):
        service_ids_exists = self.env['sale.subscription.line'].search([('service_id', '=', self.name)])
        _logger.error('Found service ids: %s %s', service_ids_exists.name, self.name)
        if len(service_ids_exists) == 1:
            if not self.portability_number:
                return
            else:
                old_name = service_ids_exists.name
                port_num_start = service_ids_exists.name.find('\n(PAC:')
                port_num_end = service_ids_exists.name.find(')', port_num_start, port_num_start + 16)
                old_portability_number = service_ids_exists.name[port_num_start: port_num_end + 1]
                _logger.error("Found PAC at: %s and ends at: %s being: %s", port_num_start, port_num_end, old_portability_number)


                service_ids_exists.name = old_name.replace(old_portability_number, '')


                comment = "\n(PAC: "
                service_ids_exists.name += comment + self.portability_number + ')'
