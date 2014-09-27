
import sys
import os
import sqlite3

def root():
   root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   return root

DB_PATH = os.path.join(os.path.dirname(__file__), 'test.db')

from libmailenator.sqlitewrapper import PendingSend
from libmailenator.mailer import Mailer

def ensure_db(db_path = DB_PATH):
    from subprocess import check_call
    make_db_script = os.path.join(root(), 'scripts', 'make_db.sh')
    check_call([make_db_script, db_path])

ensure_db()

def sqlite_connect():
    return sqlite3.connect(DB_PATH)

def delete_db():
    conn = sqlite_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM outbox")
    conn.commit()

def last_email():
    conn = sqlite_connect()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox")
    row = cur.fetchone()
    assert row is not None, "Failed to get last email from SQLite."
    return PendingSend(sqlite_connect, row[0])

def last_n_emails(num):
    conn = sqlite_connect()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox LIMIT ?", (num,))
    rows = cur.fetchall()
    assert len(rows) == num, "Failed to get last %d emails from SQLite." % (num,)
    mails = []
    for row in rows:
        mails.append(PendingSend(sqlite_connect, row[0]))
    return mails

def assert_no_emails():
    conn = sqlite_connect()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM outbox")
    row = cur.fetchone()
    assert row is None, "Should not be any emails in SQLite."

def get_mailer(sender = None):
    config = {'template_dir': root()}
    mailer = Mailer(config, sqlite_connect, sender)
    return mailer

def assert_load_template(name, vars_):
    file_path = assert_template_path(name)
    mailer = get_mailer()
    subject, msg = mailer.load_template(file_path, vars_)
    assert subject
    assert msg
    assert "{" not in msg

def assert_template_path(name):
    file_path = os.path.join(root(), name + ".txt")
    assert os.path.exists(file_path), \
        "Cannot open a template {0} that doesn't exist.".format(name)
    return file_path

def template(name):
    file_path = assert_template_path(name)
    with open(file_path, 'r') as f:
        return f.readlines()
