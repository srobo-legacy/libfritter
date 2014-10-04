
from collections import namedtuple
from io import StringIO

from ..libfritter.previewer import PreviewFormatter, Previewer, UnknownRecipient

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
        self.recipient = None
        self.subject = '-subject-'

    def default_expected(self):
        return [
            ('To', None),
            ('Subject', self.subject),
            ('Body', '-$FOO-$BAR-'),
            ('Placeholders', 'bar, foo'),
        ]

class FakeLoader(object):
    def __init__(self, tpl):
        self.name = None
        self._tpl = tpl
    def load(self, name):
        self.name = name
        return self._tpl

def fake_recipient_describer(to):
    if to.startswith('known'):
        return 'all ' + to
    raise UnknownRecipient(to)

def get_previewer_data(fake_template):
    expected_name = 'dummy'
    loader = FakeLoader(fake_template)
    previewer = Previewer(loader.load, fake_recipient_describer, None)
    data = previewer.preview_data(expected_name)
    name = loader.name
    assert expected_name == name, "Passed the wrong name to the template factory."
    return data

def test_previewer_data():
    fake_template = FakeTemplate()

    data = get_previewer_data(fake_template)

    expected = fake_template.default_expected()

    assert expected == data, "Wrong placeholder data"

def test_previewer_data_recipients():
    def helper(recipient, expected_to, desc):
        fake_template = FakeTemplate()
        fake_template.recipient = recipient

        data = get_previewer_data(fake_template)

        expected = fake_template.default_expected()
        expected[0] = ('To', expected_to)

        assert expected == \
               data, \
               "Wrong placeholder data for {0}.".format(desc)

    yield helper, None, None, None
    yield helper, [], None, "empty list"
    yield helper, ['known-1', 'known-2'], 'all known-1, all known-2', "two known recipients"

def test_previewer_data_bad_recipients():
    def helper(recipient, expected_to, desc):
        fake_template = FakeTemplate()
        fake_template.recipient = recipient

        data = get_previewer_data(fake_template)

        expected = fake_template.default_expected()
        expected[0] = ('To', expected_to)
        err = "* {}".format(UnknownRecipient('nope'))
        expected.append( ('Error', err) )

        assert expected == \
               data, \
               "Wrong placeholder data for {0}.".format(desc)

    yield helper, ['nope'], None, "unknown recipient"
    yield helper, ['known', 'nope'], 'all known', "known and unknown recipient"

def test_previewer_data_no_placeholders():
    fake_template = FakeTemplate()
    fake_template.raw_body = "-body-"

    data = get_previewer_data(fake_template)

    expected = fake_template.default_expected()
    expected[2] = ('Body', fake_template.raw_body)
    expected[3] = ('Placeholders', None)

    assert expected == data, "Wrong placeholder data"

def test_previewer_data_load_failed():
    error = Exception("I'm a teapot")
    def throws(*args):
        raise error

    previewer = Previewer(throws, None, None)
    data = previewer.preview_data('fake')

    expected = [('Error', error)]

    assert expected == data, "Wrong placeholder data"

def test_previewer_returns_errors():
    error = Exception("I'm a teapot")
    def throws(*args):
        raise error

    previewer = Previewer(throws, None, StringIO())
    actual = previewer.preview('fake')

    expected = [error]

    assert expected == actual, "Wrong value returned from previewer"

def test_reuse():
    fake_template = FakeTemplate()

    loader = FakeLoader(fake_template)
    previewer = Previewer(loader.load, fake_recipient_describer, None)

    data = previewer.preview_data('fake')
    expected = fake_template.default_expected()

    assert expected == data, "Wrong placeholder data (first time)"

    fake_template.recipient = None

    data = previewer.preview_data('fake')
    expected = fake_template.default_expected()

    assert expected == data, "Wrong placeholder data (after changing recipient)"
