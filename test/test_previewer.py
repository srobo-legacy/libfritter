
from collections import namedtuple

from ..libfritter.previewer import PreviewFormatter, Previewer

def test_prev_formatter():
    def helper(tpl, expected_str, expected_keys):
        pf = PreviewFormatter()

        res = pf.format(tpl)

        assert expected_str == res

        keys = pf.used_keys
        assert expected_keys == keys

    yield helper, "Foo {bar} ", "Foo $BAR ", set(['bar'])
    yield helper, "Foo {bar} {bar} ", "Foo $BAR $BAR ", set(['bar'])

class FakeTemplate(object):
    def __init__(self):
        self.raw_body = '-{foo}-{bar}-'
        self.recipient = '-recipient-'
        self.subject = '-subject-'

    def default_expected(self):
        return [
            ('To', self.recipient),
            ('Subject', self.subject),
            ('Body', '-$FOO-$BAR-'),
            ('Placeholders', 'bar, foo'),
        ]

def test_previewer_data():
    fake_template = FakeTemplate()
    previewer = Previewer(fake_template)
    data = previewer.preview_data

    expected = fake_template.default_expected()

    assert expected == data, "Wrong placeholder data"

def test_previewer_data_no_to():
    fake_template = FakeTemplate()
    fake_template.recipient = None
    previewer = Previewer(fake_template)
    data = previewer.preview_data

    expected = fake_template.default_expected()

    assert expected == data, "Wrong placeholder data"

def test_previewer_data_no_placeholders():
    fake_template = FakeTemplate()
    fake_template.raw_body = "-body-"

    previewer = Previewer(fake_template)
    data = previewer.preview_data

    expected = fake_template.default_expected()
    expected[2] = ('Body', fake_template.raw_body)
    expected[3] = ('Placeholders', None)

    assert expected == data, "Wrong placeholder data"
