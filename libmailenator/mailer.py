
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

def load_template(template_name, template_vars):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_path = os.path.join(script_dir, "templates", template_name + ".txt")

    msg = open(temp_path, 'r').read()

    subject = msg.splitlines()[0]
    assert subject[:8] == "Subject:"
    subject = subject[8:].strip()

    msg = "\n".join(msg.splitlines()[1:])
    msg = msg.format(**template_vars)

    return subject, msg

def send_email_template(toaddr, template_name, template_vars):
    logging.info("about to send '{0}' to '{1}'.".format(template_name, toaddr))

    subject, msg = load_template(template_name, template_vars)

    return send_email(toaddr, subject, msg)

def store_template(sql_connector, toaddr, template_name, template_vars):
    logging.debug("storing pending email: '{0}' to '{1}'.".format(template_name, toaddr))
    ps = sqlitewrapper.PendingSend(sql_connector)
    ps.toaddr = toaddr
    ps.template_name = template_name
    ps.template_vars = template_vars
    ps.save()
    return ps

def try_send(ps):
    try:
        send_email_template(ps.toaddr, ps.template_name, ps.template_vars)
        ps.mark_sent()
        logging.info("sent '{0}' to '{1}'.".format(ps.template_name, ps.toaddr))
    except:
        ps.retried()
        ps.last_error = traceback.format_exc()
        logging.exception("while sending {0}.".format(ps))
    finally:
        ps.save()

def email_template(sql_connector, toaddr, template_name, template_vars):
    # always store the email
    ps = store_template(sql_connector, toaddr, template_name, template_vars)

    # see if we're meant to send it right away
    if not config.getboolean(CONFIG_ROOT, 'delayed_send'):
        try_send(ps)
