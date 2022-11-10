# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _, SUPERUSER_ID
import logging
import traceback
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'
    
    service_id = fields.Many2one(
    'sale.service.details', string='Service ID',  tracking=True)
    
    


            
    @api.onchange('service_id')
    def onchange_service_id(self):
        service_ids_exists = self.env['sale.service.details'].search([('id', '=', self.service_id.ids)])
        
        if len(service_ids_exists) != 0:
            if service_ids_exists.subscription_id:
                raise ValidationError(_('Douplicate Service ID: %s - Subscription: %s', service_ids_exists.name, service_ids_exists.subscription_id.display_name))
            


    @api.model
    def create(self, values):
        _logger.error("Create in description of sub was called")
        if values.get('product_id','service_id.portability_number') and not values.get('name'):
            line = self.new(values)
            line.onchange_product_id()
            line.onchange_service_id()
            line.onchange_portability_number()
            values['name'] = line._fields['name'].convert_to_write(line['name'], line)
        return super(SaleSubscriptionLine, self).create(values)
