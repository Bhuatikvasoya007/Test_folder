# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class JudopayController(http.Controller):
    _success_url = '/payment/judopay/return'
    _fail_url = '/payment/judopay/return'

    @http.route('/payment/judopay/return', type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def payment_judopay_success(self, **post):
        acquirer = request.env.ref('payment_judopay.payment_acquirer_judopay')
        reciept = acquirer.generate_reciept(post)
        res = request.env['payment.transaction'].sudo().form_feedback(reciept, 'judopay')
        return request.redirect('/shop/confirmation')