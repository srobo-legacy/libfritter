
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
    "A template previewer"
    def __init__(self, template_factory, writer):
        """
        Parameters
        ----------
        template_factory : callable(name)
            Will be passed the name of a template, should return an
            ``EmailTemplate`` instance.
        writer : file object
            Used to output the preview of each item.
        """
        self._template_factory = template_factory
        self._writer = writer

    def preview_data(self, template_name):
        """
        Returns the gathered data, as a dictionary of content ready to be output.

        Parameters
        ----------
        template_name : str
            The name of the template to get the preview data for, will be
            passed to the factory callable the instance was created around.
        """
        try:
            et = self._template_factory(template_name)
            body, placeholders = self._get_body(et)
            return [
                ('To', et.recipient),
                ('Subject', et.subject),
                ('Body', body),
                ('Placeholders', placeholders),
            ]
        except Exception as e:
            return [('Error', e)]

    def preview(self, template_name):
        """
        Writes a text preview of the template into the given writer.

        Parameters
        ----------
        template_name : str
            The name of the template to get the preview data for, will be
            passed to the factory callable the instance was created around.
        """
        for name, value in self.preview_data(template_name):
            value = "{}".format(value)
            lines = "\n    ".join(l for l in value.splitlines())
            content = """# {0}

    {1}

""".format(name, lines)
            if sys.version_info[0] < 3:
                # Python 2 writers can't deal with unicode characters
                content = content.encode('utf-8')
            self._writer.write(content)

    def _get_body(self, email_template):
        formatter = PreviewFormatter()
        body = formatter.format(email_template.raw_body)
        required_keys = formatter.used_keys

        if len(required_keys):
            required_keys = ', '.join(sorted(required_keys))
        else:
            required_keys = None

        return body, required_keys
