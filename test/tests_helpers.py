
from functools import partial
import os
import sqlite3

def test_root():
   root = os.path.dirname(os.path.abspath(__file__))
   return root

def root():
   root = os.path.dirname(test_root())
   return root

DB_PATH = os.path.join(test_root(), 'test.db')

from ..libfritter.sqlitewrapper import PendingSend
from ..libfritter.file_template_factory import FileTemplateFactory
from ..libfritter.mailer import Mailer

def ensure_db(db_path = DB_PATH):
    from subprocess import check_call
    make_db_script = os.path.join(root(), 'scripts', 'make_db.sh')
    check_call([make_db_script, db_path])

ensure_db()

def sqlite_connect(db_path = DB_PATH):
    return sqlite3.connect(db_path)

def delete_db(db_path = DB_PATH):
    conn = sqlite_connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM outbox")
    conn.commit()

def last_email(db_path = DB_PATH):
    conn = sqlite_connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox")
    row = cur.fetchone()
    assert row is not None, "Failed to get last email from SQLite."
    connector = partial(sqlite_connect, db_path)
    return PendingSend(connector, row[0])

def last_n_emails(num, db_path = DB_PATH):
    conn = sqlite_connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox LIMIT ?", (num,))
    rows = cur.fetchall()
    assert len(rows) == num, "Failed to get last %d emails from SQLite." % (num,)
    mails = []
    for row in rows:
        connector = partial(sqlite_connect, db_path)
        mails.append(PendingSend(connector, row[0]))
    return mails

def assert_no_emails(db_path = DB_PATH):
    conn = sqlite_connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox")
    row = cur.fetchone()
    assert row is None, "Should not be any emails in SQLite."

def template_root():
    return os.path.join(test_root(), 'templates')

def get_mailer(sender = None, delay_send = True):
    f = FileTemplateFactory(template_root())
    mailer = Mailer({}, sqlite_connect, f.load, sender, delay_send)
    return mailer

def assert_load_template(name, vars_):
    file_path = assert_template_path(name)
    mailer = get_mailer()
    subject, msg = mailer.load_template(file_path, vars_)
    assert subject
    assert msg
    assert "{" not in msg

def assert_template_path(name):
    file_path = os.path.join(template_root(), name + ".txt")
    assert os.path.exists(file_path), \
        "Cannot open a template {0} that doesn't exist.".format(name)
    return file_path

def template(name):
    file_path = assert_template_path(name)
    with open(file_path, 'r') as f:
        return f.readlines()
