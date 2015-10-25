
from unittest import TestCase

from . import tests_helpers as test_helpers
from .tests_helpers import last_email, assert_no_emails

from ..libfritter.sqlitewrapper import PendingSend

class TestMailer(TestCase):

    def setUp(self):
        test_helpers.delete_db()
        self.fake_send_email(None, None, None, None)
        self.mailer = test_helpers.get_mailer(self.fake_send_email)

    def tearDown(self):
        test_helpers.delete_db()

    def fake_send_email(self, config, to, subject, msg):
        self._to = to
        self._subject = subject
        self._msg = msg

    def test_empty_toaddr(self):
        mailer = test_helpers.get_mailer(self.fake_send_email, delay_send = True)
        exp_addr = ''
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        threw = False
        try:
            mailer.email_template(exp_addr, exp_tpl, exp_vars)
        except ValueError:
            threw = True

        assert threw, "Should have errored about the empty toaddr"

        # Should not have stored it
        assert_no_emails()

    def test_delay_send_true(self):
        mailer = test_helpers.get_mailer(self.fake_send_email, delay_send = True)
        exp_addr = 'test@example.com'
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        mailer.email_template(exp_addr, exp_tpl, exp_vars)

        assert self._to is None, "Should not have actually sent the email"

        # Should have stored it
        stored = last_email()
        toaddr = stored.toaddr
        assert exp_addr == toaddr
        tpl = stored.template_name
        assert exp_tpl == tpl
        vars = stored.template_vars
        assert exp_vars == vars

    def test_delay_send_false(self):
        mailer = test_helpers.get_mailer(self.fake_send_email, delay_send = False)
        exp_addr = 'test@example.com'
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        mailer.email_template(exp_addr, exp_tpl, exp_vars)

        assert exp_addr == self._to, "Should have actually sent the email"

        # Should also have stored it
        stored = last_email()
        toaddr = stored.toaddr
        assert exp_addr == toaddr
        tpl = stored.template_name
        assert exp_tpl == tpl
        vars = stored.template_vars
        assert exp_vars == vars

    def test_store_temaplate(self):
        exp_addr = 'test@example.com'
        exp_tpl  = 'tpl'
        exp_vars = {'foo':'bar'}
        ps = self.mailer.store_template(exp_addr, exp_tpl, exp_vars)

        assert ps.in_db

        stored = last_email()
        toaddr = stored.toaddr
        assert exp_addr == toaddr
        tpl = stored.template_name
        assert exp_tpl == tpl
        vars = stored.template_vars
        assert exp_vars == vars

    def test_load_temaplate_unicode(self):
        tpl  = 'example_template'

        e_acute = '\u00e9'
        bees = 'b{0}{0}s'.format(e_acute)
        template_vars = {"foo": bees}

        subject, msg = self.mailer.load_template(tpl, template_vars)

        assert e_acute in msg

    def test_try_send_ok(self):
        exp_addr = 'test@example.com'
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        ps = PendingSend(test_helpers.sqlite_connect)
        ps.toaddr = exp_addr
        ps.template_name = exp_tpl
        ps.template_vars = exp_vars

        self.mailer.try_send(ps)

        tpl_lines = test_helpers.template(exp_tpl)
        exp_subject = tpl_lines[0]

        assert exp_addr == self._to
        assert self._subject in exp_subject
        assert 'foo' not in self._msg
        assert 'bar' in self._msg

        ps_stored = PendingSend(test_helpers.sqlite_connect, ps.id)

        sent = ps_stored.is_sent
        assert sent

    def test_try_send_throws(self):
        exp_addr = 'test@example.com'
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        ps = PendingSend(test_helpers.sqlite_connect)
        ps.toaddr = exp_addr
        ps.template_name = exp_tpl
        ps.template_vars = exp_vars

        exc_msg = "I am a teapot"
        def throws(cfg, to, subject, msg):
            raise Exception(exc_msg)

        mailer = test_helpers.get_mailer(throws)
        mailer.try_send(ps)

        ps_stored = PendingSend(test_helpers.sqlite_connect, ps.id)

        sent = ps_stored.is_sent
        assert not sent
        last_error = ps_stored.last_error
        assert exc_msg in last_error
        retries = ps_stored.retry_count
        assert 1 == retries

    def test_try_send_save_throws(self):
        exp_addr = 'test@example.com'
        exp_tpl  = 'example_template'
        exp_vars = {'foo':'bar'}

        ps = PendingSend(test_helpers.sqlite_connect)
        ps.toaddr = exp_addr
        ps.template_name = exp_tpl
        ps.template_vars = exp_vars

        exc_msg = "I am a teapot"
        def throws():
            raise Exception(exc_msg)

        ps.save = throws

        mailer = test_helpers.get_mailer(self.fake_send_email)
        mailer.try_send(ps)

        # 'assert' that no errors were passed upwards
