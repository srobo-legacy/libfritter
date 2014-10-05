
from __future__ import unicode_literals

import string
import sys

class UnknownRecipient(Exception):
    def __init__(self, recipient, detail = None):
        detail_msg = ''
        if detail:
            detail_msg = ": {}".format(detail)
        super(UnknownRecipient, self).__init__(
            "Unknown recipient '{}'.".format(recipient, detail_msg)
        )
        self._recipient = recipient
        self._detail = detail

    @property
    def detail(self):
        return self._detail

    @property
    def recipient(self):
        return self._recipient

class PreviewFormatter(string.Formatter):
    def __init__(self):
        self.used_keys = set()

    def get_value(self, key, args, kwargs):
        self.used_keys.add(key)
        return "$" + key.upper()

class Previewer(object):
    @staticmethod
    def format_section(heading, content):
        """Formats a section with a heading.

        Parameters
        ----------
        heading : str
            The name of the section
        content : object
            The content of the section. Each line of content will be
            indented by four spaces.

        Returns
        -------
        str
            The formatted section. This includes two empty lines at the
            end so that values are suitable for ``join``ing together with
            a gap in between.
        """
        content_str = "{}".format(content)
        lines = "\n    ".join(l for l in content_str.splitlines())
        return """# {0}

    {1}

""".format(heading, lines)

    "A template previewer"
    def __init__(self, template_factory, recipient_checker, writer):
        """
        Parameters
        ----------
        template_factory : callable(name)
            Will be passed the name of a template, should return an
            ``EmailTemplate`` instance.
        recipient_checker : callable(recipient)
            Will be passed a value from the "To:" line of the template,
            should return a description of the recipient or raise
            ``UnknownRecipient``.
        writer : file object
            Used to output the preview of each item.
        """
        self._template_factory = template_factory
        self._recipient_checker = recipient_checker
        self._writer = writer

    def preview_data(self, template_name):
        """
        Returns the gathered data, as a list of content tuples ready to be output.

        Parameters
        ----------
        template_name : str
            The name of the template to get the preview data for, will be
            passed to the factory callable the instance was created around.
        """
        try:
            et = self._template_factory(template_name)
            recipients, recipient_errors = self._get_recipients(et.recipient)
            body, placeholders, body_error = self._get_body(et)
            items = [
                ('To', recipients),
                ('Subject', et.subject),
                ('Body', body),
                ('Placeholders', placeholders),
            ]

            errors = []
            if recipient_errors:
                errors += recipient_errors

            if body_error:
                errors.append(body_error)

            if errors:
                error_msg = "\n* ".join("{}".format(e) for e in errors)
                items.append( ('Error', '* ' + error_msg) )

            return items
        except Exception as e:
            return [('Error', e)]

    def preview(self, template_name, writer = None):
        """
        Writes a text preview of the template into the given writer.

        Parameters
        ----------
        template_name : str
            The name of the template to get the preview data for, will be
            passed to the factory callable the instance was created around.
        writer : file object, optional
            Used to output the preview of each item in preference to the
            writer given to the instance when it was created.

        Returns
        -------
        str or None
            The content of the errors section, if any.
        """
        if not writer:
            writer = self._writer

        errors_value = None
        for name, value in self.preview_data(template_name):
            content = self.format_section(name, value)
            if sys.version_info[0] < 3:
                # Python 2 writers can't deal with unicode characters
                content = content.encode('utf-8')
            writer.write(content)
            if name == 'Error':
                errors_value = "{}".format(value)

        return errors_value

    def _get_body(self, email_template):
        try:
            formatter = PreviewFormatter()
            body = formatter.format(email_template.raw_body)
            required_keys = formatter.used_keys
        except Exception as e:
            return None, None, e

        if len(required_keys):
            required_keys = ', '.join(sorted(required_keys))
        else:
            required_keys = None

        return body, required_keys, None

    def _get_recipients(self, recipient_list):
        if not recipient_list:
            return None, None

        descriptions = []
        errors = []
        for r in recipient_list:
            try:
                desc = self._recipient_checker(r)
                descriptions.append(desc)
            except UnknownRecipient as e:
                errors.append(e)

        descriptions_str = None
        if descriptions:
            descriptions_str = ', '.join(descriptions)
        return descriptions_str, errors
