# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import datetime
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

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'
    



    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        company = self.env.company or line.analytic_account_id.company_id
        tax_ids = line.product_id.taxes_id.filtered(lambda t: t.company_id == company)
        price_unit = line.price_unit
        if fiscal_position and tax_ids:
            tax_ids = self.env['account.fiscal.position'].browse(fiscal_position).map_tax(tax_ids)
            price_unit = self.env['account.tax']._fix_tax_included_price_company(line.price_unit, line.product_id.taxes_id, tax_ids, self.company_id)
        values = {
            'name': line.name,
            'subscription_id': line.analytic_account_id.id,
            'price_unit': price_unit or 0.0,
            'discount': line.discount,
            'quantity': line.quantity,
            'product_uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'tax_ids': [(6, 0, tax_ids.ids)],
            'subscription_start_date': date_start,
            'subscription_end_date': date_stop,
            'service_id_invoice': line.service_id.id
        }
        # only adding analytic_account_id and tag_ids if they exist in the sale.subscription.
        # if not, they will be computed used the analytic default rule
        if line.analytic_account_id.analytic_account_id.id:
            values.update({'analytic_account_id': line.analytic_account_id.analytic_account_id.id})
        if line.analytic_account_id.tag_ids.ids:
            values.update({'analytic_tag_ids': [(6, 0, line.analytic_account_id.tag_ids.ids)]})
        return values
    
    
    def action_service_ids(self):
        self.ensure_one()
        service_ids = self.env['sale.service.details'].search([('subscription_id.id', 'in', self.ids)])
        _logger.error('Found service ids: %s', service_ids)
        action = self.env["ir.actions.actions"]._for_xml_id("service_id.sale_service_details_action")
        action["context"] = {
            "create": False,
        }
        if len(service_ids) > 1:
            action['domain'] = [('id', 'in', service_ids.ids)]
        elif len(service_ids) == 1:
            form_view = [(self.env.ref('service_id.sale_service_details_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = service_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action