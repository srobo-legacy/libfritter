
from email.mime.text import MIMEText
import logging
import smtplib
import traceback
import os

from . import sqlitewrapper
from . import email_template
from . import template_source

CONFIG_ROOT = 'mailer'

def send_email(config, toaddr, subject, msg):
    """Sends an email.

    Parameters
    ----------
    config : dict_like
        Must have the following keys:
        * `fromaddr` - the senders address
        * `smtpserver` - the server to send the email via
        * `username` - the username for the server
        * `password` - the password for the server
    toaddr : str
    subject : str
    msg : str
    """
    fromaddr = config['fromaddr']
    msg = MIMEText(msg)
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg["Subject"] = subject

    server = smtplib.SMTP_SSL(config['smtpserver'], timeout = 5)
    smtp_user = config['username']
    smtp_pass = config['password']
    server.login(smtp_user, smtp_pass)

    r = server.sendmail(fromaddr, toaddr, str(msg))

    try:
        server.quit()
    except smtplib.sslerror:
        pass

    return len(r) > 0

class Mailer(object):
    def __init__(self, config, sql_connector, sender = None):
        """
        Parameters
        ----------
        config : dict_like
            Must have the keys as needed by the `sender`, plus:
            * `template_dir`: str - path to the directory containing the templates
            * `delayed_send`: bool - if `true` will cache the templated
                                     email request and send it later, otherwise
                                     will attempt to send the email immediately
        sql_connector : callable
            Returning a sqlite connection
        sender : callable, optional
            Used to actually send the email. Defaults to `send_email`.
        """
        self._config = config
        self._sql_connector = sql_connector
        self._sender = sender or send_email

    def send_email(self, toaddr, subject, msg):
        return self._sender(self._config, toaddr, subject, msg)

    def load_template(self, template_name, template_vars):
        source = template_source.FileTemaplateSource(self._config['template_dir'])
        raw_template = source.load(template_name)

        et = email_template.EmailTemplate(raw_template)
        subject = et.subject
        msg = et.format(template_vars)

        return subject, msg

    def send_email_template(self, toaddr, template_name, template_vars):
        logging.info("about to send '{0}' to '{1}'.".format(template_name, toaddr))

        subject, msg = self.load_template(template_name, template_vars)

        return self.send_email(toaddr, subject, msg)

    def store_template(self, toaddr, template_name, template_vars):
        logging.debug("storing pending email: '{0}' to '{1}'.".format(template_name, toaddr))
        ps = sqlitewrapper.PendingSend(self._sql_connector)
        ps.toaddr = toaddr
        ps.template_name = template_name
        ps.template_vars = template_vars
        ps.save()
        return ps

    def try_send(self, ps):
        try:
            self.send_email_template(ps.toaddr, ps.template_name, ps.template_vars)
            ps.mark_sent()
            logging.info("sent '{0}' to '{1}'.".format(ps.template_name, ps.toaddr))
        except:
            ps.retried()
            ps.last_error = traceback.format_exc()
            logging.exception("while sending {0}.".format(ps))
        finally:
            ps.save()

    def email_template(self, toaddr, template_name, template_vars):
        # always store the email
        ps = self.store_template(toaddr, template_name, template_vars)

        # see if we're meant to send it right away
        if not self._config['delayed_send']:
            self.try_send(ps)
