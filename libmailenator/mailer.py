
from email.mime.text import MIMEText
import logging
import smtplib
import traceback
import os

from config import config
import sqlitewrapper

CONFIG_ROOT = 'mailer'

def send_email(toaddr, subject, msg):
    fromaddr = config.get(CONFIG_ROOT, 'fromaddr')
    msg = MIMEText(msg)
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg["Subject"] = subject

    server = smtplib.SMTP_SSL(config.get(CONFIG_ROOT, 'smtpserver'), timeout = 5)
    smtp_user = config.get(CONFIG_ROOT, 'username')
    smtp_pass = config.get(CONFIG_ROOT, 'password')
    server.login(smtp_user, smtp_pass)

    r = server.sendmail(fromaddr, toaddr, str(msg))

    try:
        server.quit()
    except smtplib.sslerror:
        pass

    return len(r) > 0

class Mailer(object):
    def __init__(self, config, sql_connector, sender = None):
        self._config = config
        self._sql_connector = sql_connector
        self._sender = sender or send_email

    def send_email(self, toaddr, subject, msg):
        return self._sender(self._config, toaddr, subject, msg)

    def template_path(self, template_name):
        template_dir = self._config.get(CONFIG_ROOT, 'template_dir')
        temp_path = os.path.join(template_dir, template_name + ".txt")
        return temp_path

    def load_template(self, template_name, template_vars):
        temp_path = self.template_path(template_name)

        msg = open(temp_path, 'r').read()

        subject = msg.splitlines()[0]
        assert subject[:8] == "Subject:"
        subject = subject[8:].strip()

        msg = "\n".join(msg.splitlines()[1:])
        msg = msg.format(**template_vars)

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
        if not self._config.get(CONFIG_ROOT, 'delayed_send'):
            self.try_send(ps)
