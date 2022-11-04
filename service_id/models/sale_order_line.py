# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import traceback

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    service_id = fields.Many2one(
    'sale.service.details', string='Service ID')
    

    def _prepare_subscription_line_data(self):
        """Prepare a dictionnary of values to add lines to a subscription."""
        values = list()
        for line in self:
            values.append((0, False, {
                'product_id': line.product_id.id,
                'name': line.name,
                'service_id': line.service_id.id,
                'quantity': line.product_uom_qty,
                'uom_id': line.product_uom.id,
                'price_unit': line.price_unit,
                'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
            }))
        return values
    
    def _update_subscription_line_data(self, subscription):
        """Prepare a dictionnary of values to add or update lines on a subscription."""
        values = list()
        dict_changes = dict()
        for line in self:
            service_id = line.service_id.id
            sub_line = subscription.recurring_invoice_line_ids.filtered(
                lambda l: (l.product_id, l.uom_id, l.price_unit) == (line.product_id, line.product_uom, line.price_unit)
            )
            if service_id:
                 # we create a new line in the subscription: (0, 0, values)
                values.append(line._prepare_subscription_line_data()[0])
            else:
                if sub_line:
                    # We have already a subscription line, we need to modify the product quantity
                    if len(sub_line) > 1:
                        # we are in an ambiguous case
                        # to avoid adding information to a random line, in that case we create a new line
                        # we can simply duplicate an arbitrary line to that effect
                        sub_line[0].copy({'name': line.display_name, 'quantity': line.product_uom_qty})
                    else:
                        dict_changes.setdefault(sub_line.id, sub_line.quantity)
                        # upsell, we add the product to the existing quantity
                        dict_changes[sub_line.id] += line.product_uom_qty
                else:
                    # we create a new line in the subscription: (0, 0, values)
                    values.append(line._prepare_subscription_line_data()[0])

        values += [(1, sub_id, {'quantity': dict_changes[sub_id]}) for sub_id in dict_changes]
        return values

    
