# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from libfritter.template_source import FileTemaplateSource

from tests_helpers import assert_template_path, template_root

def load_template(name):
    path = assert_template_path(name)
    root = template_root()
    content = FileTemaplateSource(root).load(name)
    return content

def test_subject():
    def helper(name, lineno, expected):
        content = load_template(name)
        line = content.splitlines()[lineno]

        assert expected == line

    yield helper, 'template-1', 0, "Subject: Sam likes ponys ♘."
    yield helper, 'template-2', 1, "Subject: Something's happening"
