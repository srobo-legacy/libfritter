
import os
import sys

class InvalidTemplateException(Exception):
    pass

class EmailTemplate(object):
    "A class which loads and prepares a template for sending"
    def __init__(self, template_content):
        """Create a new template around the given id.

        Parameters
        ----------
        template_content : str
            The raw content of the template.
        """

        self._content = template_content
        self._tpl_to = None
        self._tpl_subj = None
        self._tpl_body = None

    def _process_lines(self, lines):
        subj_prefix = "Subject:"
        to_prefix = "To:"
        newline = "\n"

        next_line = lines.pop(0)
        if not next_line.startswith(subj_prefix):
            if not next_line.startswith(to_prefix):
                msg = "Template first line must start with either '{0}' " \
                      "or '{1}', got: '{2}'.".format(to_prefix, subj_prefix, next_line)
                raise InvalidTemplateException(msg)

            tpl_to = next_line[len(to_prefix):].strip()
            self._tpl_to = [r.strip() for r in tpl_to.split(',')]
            next_line = lines.pop(0)

        if not next_line.startswith(subj_prefix):
            msg = "Template must contain a subject within its first two lines."
            raise InvalidTemplateException(msg)

        self._tpl_subj = next_line[len(subj_prefix):].strip()

        stripped_lines = [l.rstrip() for l in lines]
        self._tpl_body = newline.join(stripped_lines).strip(newline)

    def _load(self):
        if self._tpl_subj is None:
            self._process_lines(self._content.splitlines())

    @property
    def raw_body(self):
        self._load()
        return self._tpl_body

    @property
    def recipient(self):
        self._load()
        return self._tpl_to

    @property
    def subject(self):
        self._load()
        return self._tpl_subj

    def format(self, args):
        msg = self.raw_body.format(**args)
        return msg
