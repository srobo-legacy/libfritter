
from email.mime.text import MIMEText
import logging
import smtplib
import traceback

from . import sqlitewrapper

CONFIG_ROOT = 'mailer'

def send_email(config, toaddr, subject, msg):
    """Sends an email.

    Parameters
    ----------
    config : dict_like
        Must have the following keys:
        * ``fromaddr`` - the senders address
        * ``smtpserver`` - the server to send the email via
        * ``username`` - the username for the server
        * ``password`` - the password for the server
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
    def __init__(self, config, sql_connector, template_factory, sender = None,
                 delay_send = True):
        """
        Parameters
        ----------
        config : object
            Configuration object which will be passed as the first parameter
            to the ``sender`` callable.
        sql_connector : callable
            Returning a sqlite connection
        template_factory : callable(name)
            Will be passed the name of a template, should return an
            ``EmailTemplate`` instance.
        sender : callable, optional
            Used to actually send the email. Defaults to ``send_email``.
        delay_send : bool, optional
            Whether or not to delay all sending of emails. Defaulting to
            ``True``, this means that when asked to send an email this class
            will instead cache it (via the provided SQL connection) for
            sending later.
            This avoids potentially length delays for the caller, at the
            expense of the email not being sent immediately.
        """
        self._config = config
        self._sql_connector = sql_connector
        self._template_factory = template_factory
        self._sender = sender or send_email
        self._delay_send = delay_send

    def send_email(self, toaddr, subject, msg):
        return self._sender(self._config, toaddr, subject, msg)

    def load_template(self, template_name, template_vars):
        et = self._template_factory(template_name)
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
        """Prepare a new email based on a template.
        This is expected to be the main entry point for sending new emails.

        Parameters
        ----------
        toaddr : str
            The email addresss to send the email to.
        template_name : str
            The identifier for the template to use. Will be passed to the
            template_factory this mailer was created with.
        template_vars : dict
            A map of values to format the template's body with.
        """
        # always store the email
        ps = self.store_template(toaddr, template_name, template_vars)

        # see if we're meant to send it right away
        if not self._delay_send:
            self.try_send(ps)
