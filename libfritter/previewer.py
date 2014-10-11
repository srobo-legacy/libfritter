
from __future__ import unicode_literals

import string
import sys

ERRORS_HEADING = 'Errors'

class UnknownRecipient(Exception):
    def __init__(self, recipient, detail = None):
        detail_msg = ''
        if detail:
            detail_msg = ": {}".format(detail)
        super(UnknownRecipient, self).__init__(
            "Unknown recipient '{0}'{1}.".format(recipient, detail_msg)
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
    def __init__(self, valid_keys = None):
        """Create a new magic formatter

        Parameters
        ----------
        valid_keys : list, optional
            A list of valid placeholders. If not passed then all placeholders
            are considered valid.
        """
        self._valid_keys = set(valid_keys or [])
        self.used_keys = set()

    def get_value(self, key, args, kwargs):
        self.used_keys.add(key)
        prefix = '$'
        if self._valid_keys and key not in self._valid_keys:
            prefix += "INVALID_"
        return prefix + key.upper()

    @property
    def invalid_keys(self):
        "The set of keys which were invalid."
        if self._valid_keys:
            return self.used_keys - self._valid_keys
        else:
            return set()

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

    @staticmethod
    def list_or_none(l, template = '{}'):
        if l:
            return template.format(', '.join(sorted(l)))
        else:
            return None

    "A template previewer"
    def __init__(self, template_factory, recipient_checker, writer,
                 valid_placeholders = None, require_recipients = False):
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
        valid_placeholders : list, optional
            A list of valid placeholders. If not passed then all placeholders
            are considered valid.
        require_recipients : bool
            Whether or not some recipients are required.
        """
        self._template_factory = template_factory
        self._recipient_checker = recipient_checker
        self._writer = writer
        self._valid_placeholders = set(valid_placeholders or [])
        self._require_recipients = require_recipients

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
            body, used_placeholders, body_error = self._get_body(et)

            if self._valid_placeholders:
                placeholders = [
                    ('Restricted to', self.list_or_none(self._valid_placeholders)),
                    ('Used', used_placeholders),
                ]
            else:
                placeholders = used_placeholders

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
                items.append( (ERRORS_HEADING, '* ' + error_msg) )

            return items
        except Exception as e:
            return [(ERRORS_HEADING, e)]

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
            content = value
            if isinstance(value, list):
                content = "".join(self.format_section(n, v) for n, v in value)
                # Strip the final newline since one gets added below as well
                if content:
                    assert content[-1] == "\n"
                    content = content[:-1]

            content = self.format_section(name, content)
            if sys.version_info[0] < 3:
                # Python 2 writers can't deal with unicode characters
                content = content.encode('utf-8')
            writer.write(content)
            if name == ERRORS_HEADING:
                errors_value = "{}".format(value)

        return errors_value

    def _get_body(self, email_template):
        formatter = PreviewFormatter(self._valid_placeholders)
        try:
            body = formatter.format(email_template.raw_body)
        except Exception as e:
            return None, None, e

        required_keys = self.list_or_none(formatter.used_keys)
        bad_keys = self.list_or_none(formatter.invalid_keys, "Invalid placeholder(s): {}.")

        return body, required_keys, bad_keys

    def _get_recipients(self, recipient_list):
        if not recipient_list:
            if self._require_recipients:
                return None, ['No recipients specified, but are required']
            else:
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
