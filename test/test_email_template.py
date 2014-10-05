# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from ..libfritter.email_template import EmailTemplate, InvalidTemplateException
from ..libfritter.file_template_factory import FileTemplateFactory

from .tests_helpers import assert_template_path, template_root

def load_template(name):
    assert_template_path(name)
    root = template_root()
    f = FileTemplateFactory(root)
    et = f.load(name)
    return et

def test_formatted_body():
    et = load_template('template-1')

    replacement = 'bacon'
    placeholder = 'placeholder'
    args = {placeholder: replacement}
    body = et.format(args)
    assert "{" not in body
    assert placeholder not in body
    assert replacement in body

def test_raw_body():
    et = load_template('template-1')

    placeholder = 'placeholder'
    body = et.raw_body
    assert "{" in body
    assert placeholder in body

def test_subject():
    def helper(name, expected):
        et = load_template(name)

        subj = et.subject
        assert expected == subj

    yield helper, 'template-1', "Sam likes ponys ♘."
    yield helper, 'template-2', "Something's happening"

def test_to():
    def helper(name, expected):
        et = load_template(name)

        to = et.recipient
        assert expected == to

    yield helper, 'template-1', None
    yield helper, 'template-2', ["students"]
    yield helper, 'template-3', ["students", "team-leaders"]

def assert_invalid(et, name):
    threw = False
    try:
        print(et.subject)
    except InvalidTemplateException:
        threw = True

    assert threw, "Should have failed to load template '{0}'".format(name)

def test_invalid():
    def helper(name):
        et = load_template(name)
        assert_invalid(et, name)

    yield helper, "invalid-1"
    yield helper, "invalid-2"
    yield helper, "invalid-3"

def test_invalid_too_short():
    et = EmailTemplate("To: jim")
    assert_invalid(et, 'too short')

def test_strip_empty_start_end_lines():
    et = load_template('template-3')

    body = et.raw_body
    lines = body.splitlines()

    first = lines[0]
    last = lines[-1]

    assert '    TEST-TOP' == first, "Wrong first line"
    assert 'TEST-BOTTOM' == last, "Wrong last line"

    num_lines = len(lines)
    assert num_lines == 16, "Should not have changed the middle lines"
