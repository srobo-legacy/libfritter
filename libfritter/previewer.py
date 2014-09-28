
from __future__ import unicode_literals

import string
import sys

class PreviewFormatter(string.Formatter):
    def __init__(self):
        self.used_keys = set()

    def get_value(self, key, args, kwargs):
        self.used_keys.add(key)
        return "$" + key.upper()

class Previewer(object):
    "A previewer for EmailTemplate instances"
    def __init__(self, email_template):
        self._et = email_template
        self._body = None
        self._required_keys = None

    @property
    def preview_data(self):
        """
        Returns the gathered data, as a dictionary of content ready to be output.
        """
        items = [
            ('To', self._et.recipient),
            ('Subject', self._et.subject),
            ('Body', self.get_body()),
            ('Placeholders', self.get_placeholders()),
        ]
        return items

    def preview(self, writer):
        """
        Writes a text preview of the template into the given writer.
        """
        for name, value in self.preview_data:
            value = "{}".format(value)
            lines = "\n    ".join(l for l in value.splitlines())
            content = """# {0}

    {1}

""".format(name, lines)
            if sys.version_info[0] < 3:
                # Python 2 writers can't deal with unicode characters
                content = content.encode('utf-8')
            writer.write(content)

    def do_format(self):
        if self._body is None:
            formatter = PreviewFormatter()
            self._body = formatter.format(self._et.raw_body)
            self._required_keys = formatter.used_keys

    def get_body(self):
        self.do_format()
        return self._body

    def get_placeholders(self):
        self.do_format()
        if self._required_keys:
            return ', '.join(sorted(self._required_keys))
        return None
