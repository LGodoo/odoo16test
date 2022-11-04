# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import traceback

_logger = logging.getLogger(__name__)


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'
    
    service_id = fields.Many2one(
    'sale.service.details', string='Service ID')
    
    

    
    @api.onchange('service_id.portability_number')
    def onchange_portability_number(self):
        if not self.service_id.portability_number:
            return
        else:
            old_name = self.name
            port_num_start = self.name.find('\n(PAC:')
            port_num_end = self.name.find(')', port_num_start, port_num_start + 16)
            old_portability_number = self.name[port_num_start: port_num_end + 1]
            _logger.error("Found PUK at: %s and ends at: %s being: %s", port_num_start, port_num_end, old_portability_number)
            
        
            self.name = old_name.replace(old_portability_number, '')
            
            
            comment = "\n(PAC: "
            self.name += comment + self.service_id.portability_number + ')'

            
    @api.onchange('service_id')
    def onchange_service_id(self):
        self.onchange_portability_number()

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
