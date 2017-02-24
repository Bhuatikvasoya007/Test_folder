# -*- coding: utf-8 -*-
from lxml import objectify
import odoo
from odoo.addons.payment.tests.common import PaymentAcquirerCommon
from odoo.tools import mute_logger


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class JudopayCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(JudopayCommon, self).setUp()

        self.judopay = self.env.ref('payment_judopay.payment_acquirer_judopay')


class JudopayForm(JudopayCommon):

    def test_10_judopay_form_render(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        self.assertEqual(self.judopay.environment, 'test',
                         'test without test environment')

        form_values = {
            'reference': "4QcAAAIAAAAQAAAACAAAABeVZ4JmdHsgYfhr4UWspql482AsJRb3Pim2vFCgMOG41ZnYlQ",
        }
        res = self.judopay.render(
            'test_ref0', 0.01, self.currency_euro.id, values=form_values, partner_id=self.env.user.id)
        tree = objectify.fromstring(res)
        self.assertEqual(tree.get(
            'action'), 'https://pay.judopay-sandbox.com/v1', 'Judopay: wrong form POST url')

    @mute_logger('odoo.addons.payment_judopay.models.payment_judopay', 'ValidationError')
    def test_20_judopay_form_management(self):
        self.assertEqual(self.judopay.environment, 'test',
                         'test without test environment')
        tx = self.env['payment.transaction'].create({
            'amount': 1.95,
            'acquirer_id': self.judopay.id,
            'currency_id': self.currency_euro.id,
            'reference': 'test_ref0',
            'partner_country_id': self.country_france.id
        })
        judopay_post_data = {
            u'yourPaymentReference': u'test_ref0',
            u'status': u'success',
            u'reference': u'4QcAAAIAAAAQAAAACAAAABeVZ4JmdHsgYfhr4UWspql482AsJRb3Pim2vFCgMOG41ZnYlQ',
            u'receipt': {'receiptId':'1234567890'},
        }
        tx.form_feedback(judopay_post_data, 'judopay')
        self.assertEqual(tx.state, 'done', 'judopay: wrong state after receiving a valid pending notification')
        tx.write({'state': 'draft', 'acquirer_reference': False})
        tx.form_feedback(judopay_post_data, 'judopay')
