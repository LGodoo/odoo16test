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
    
    
    def _prepare_renewal_order_values(self, discard_product_ids=False, new_lines_ids=False):
        res = dict()
        for subscription in self:
            subscription = subscription.with_company(subscription.company_id)
            order_lines = []
            fpos = subscription.env['account.fiscal.position'].get_fiscal_position(subscription.partner_id.id)
            partner_lang = subscription.partner_id.lang
            if discard_product_ids:
                # Prevent to add products discarded during the renewal
                line_ids = subscription.with_context(active_test=False).recurring_invoice_line_ids.filtered(
                    lambda l: l.product_id.id not in discard_product_ids)
            else:
                line_ids = subscription.recurring_invoice_line_ids
            for line in line_ids:
                product = line.product_id.with_context(lang=partner_lang) if partner_lang else line.product_id
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': product.with_context(active_test=False).get_product_multiline_description_sale(),
                    'service_id': line.service_id.id,
                    'subscription_id': subscription.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                }))
            if new_lines_ids:
                # Add products during the renewal (sort of upsell)
                for line in new_lines_ids:
                    existing_line_ids = subscription.recurring_invoice_line_ids.filtered(
                        lambda l: l.product_id.id == line.product_id.id)
                    if existing_line_ids:
                        # The product already exists in the SO lines, update the quantity
                        def _update_quantity(so_line):
                            # Map function to update the quantity of the SO line.
                            if so_line[2]['product_id'] in existing_line_ids.mapped('product_id').ids:
                                so_line[2]['product_uom_qty'] = line.quantity + so_line[2]['product_uom_qty']
                            return so_line
                        # Update the order lines with the new quantity
                        order_lines = list(map(_update_quantity, order_lines))
                    else:
                        order_lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'service_id': line.service_id.id,
                            'subscription_id': subscription.id,
                            'product_uom': line.uom_id.id,
                            'product_uom_qty': line.quantity,
                            'price_unit': subscription.pricelist_id.with_context(uom=line.uom_id.id).get_product_price(
                                line.product_id, line.quantity, subscription.partner_id),
                            'discount': 0,
                        }))
            addr = subscription.partner_id.address_get(['delivery', 'invoice'])
            res[subscription.id] = {
                'pricelist_id': subscription.pricelist_id.id,
                'partner_id': subscription.partner_id.id,
                'partner_invoice_id': subscription.partner_invoice_id.id or addr['invoice'],
                'partner_shipping_id': subscription.partner_shipping_id.id or addr['delivery'],
                'currency_id': subscription.pricelist_id.currency_id.id,
                'order_line': order_lines,
                'analytic_account_id': subscription.analytic_account_id.id,
                'subscription_management': 'renew',
                'origin': subscription.code,
                'note': subscription.description,
                'fiscal_position_id': fpos.id,
                'user_id': subscription.user_id.id,
                'payment_term_id': subscription.payment_term_id.id,
                'company_id': subscription.company_id.id,
            }
        return res