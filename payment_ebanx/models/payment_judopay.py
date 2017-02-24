# -*- coding: utf-'8' "-*-"
import base64
import json
import logging
import requests
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class AcquirerJudopay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('judopay', 'JudoPay')])
    judopay_id = fields.Char(string="Judo id")
    judopay_token = fields.Char(string="Token")
    judopay_secret = fields.Char(string="Secret")

    @api.model
    def _get_judopay_urls(self, environment):
        if environment == 'prod':
            return {
                'judopay_form_url': 'https://pay.judopay.com/v1',
                'judopay_api_url': 'https://gw1.judopay.com/webpayments/payments',
                'judopay_reciept_url': 'https://gw1.judopay.com/webpayments/'
            }
        else:
            return {
                'judopay_form_url': 'https://pay.judopay-sandbox.com/v1',
                'judopay_api_url': 'https://gw1.judopay-sandbox.com/webpayments/payments',
                'judopay_reciept_url': 'https://gw1.judopay-sandbox.com/webpayments/',
            }

    @api.multi
    def judopay_get_form_action_url(self):
        return self._get_judopay_urls(self.environment)['judopay_form_url']

    @api.multi
    def judopay_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        judopay_tx_values = dict(values)
        judopay_form_values = {
            'reference': self.judopay_reference(values)
        }
        return judopay_form_values

    @api.multi
    def judopay_reference(self, values):
        api_url = self._get_judopay_urls(self.environment)['judopay_api_url']
        auth = "%s:%s" % (self.judopay_token, self.judopay_secret)
        b64Val = base64.b64encode(auth)
        headers = {"API-Version": "5.2", "Content-Type": "application/json",
                   "Accept": "application/json", "Authorization": "Basic %s" % b64Val}
        data = {"judoId": self.judopay_id, "amount": values['amount'], "partnerServiceFee": "", "yourConsumerReference": values['billing_partner'].id, "yourPaymentReference":
                values['reference'], "yourPaymentMetaData": "", "clientIpAddress": "", "clientUserAgent": "", "currency": values['currency'] and values['currency'].name or ''}
        data = json.dumps(data)
        res = requests.post(api_url, headers=headers, data=data).json()
        return res.get('reference')

    @api.multi
    def generate_reciept(self, data):
        api_url = self._get_judopay_urls(self.environment)['judopay_reciept_url']
        api_url += '/%s' % (data.get('Reference'))
        auth = "%s:%s" % (self.judopay_token, self.judopay_secret)
        b64Val = base64.b64encode(auth)
        headers = {"API-Version": "5.2", "Content-Type": "application/json",
                   "Authorization": "Basic %s" % b64Val}
        res = requests.get(api_url, headers=headers).json()
        return res


class TxJudopay(models.Model):
    _inherit = 'payment.transaction'

    judopay_receipt_id = fields.Char(string="Judopay Receipt ID")
    judopay_reference_key = fields.Char(string="Judopay Reference Key")

    @api.multi
    def _judopay_form_get_tx_from_data(self, data):
        reference = data.get('yourPaymentReference')
        if not reference:
            error_msg = _('Judopay: received data with missing order')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        txs = self.env['payment.transaction'].search(
            [('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Judopay: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    @api.multi
    def _judopay_form_validate(self, data):
        if (data.get('status').lower() == "success"):
            self.write({'state': 'done', 'judopay_reference_key': data.get(
                'reference'), 'judopay_receipt_id': data.get('receipt')['receiptId']})
        elif (data.get('status').lower() == "open"):
            self.write(
                {'state': 'error', 'judopay_reference_key': data.get('reference')})
        elif (data.get('status').lower() == "cancelled"):
            self.write(
                {'state': 'cancel', 'judopay_reference_key': data.get('reference')})
        else:
            self.write(
                {'state': 'error', 'judopay_reference_key': data.get('reference')})