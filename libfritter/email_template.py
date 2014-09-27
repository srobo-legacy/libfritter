
import os

import sys
if sys.version_info[0] < 3:
    import codecs
    open_ = codecs.open
else:
    open_ = open

class InvalidTemplateException(Exception):
    pass

class EmailTemplate(object):
    "A class which loads and prepares a template for sending"
    def __init__(self, path):
        self._path = path
        self._tpl_to = None
        self._tpl_subj = None
        self._tpl_body = None

    def _load_lines(self, lines):
        subj_prefix = "Subject:"
        to_prefix = "To:"

        next_line = lines.pop(0)
        if not next_line.startswith(subj_prefix):
            if not next_line.startswith(to_prefix):
                msg = "Template first line must start with either '{0}' " \
                      "or '{1}', got: '{2}'.".format(to_prefix, subj_prefix, next_line)
                raise InvalidTemplateException(msg)

            self._tpl_to = next_line[len(to_prefix):].strip()
            next_line = lines.pop(0)

        if not next_line.startswith(subj_prefix):
            msg = "Template must contain a subject within its first two lines."
            raise InvalidTemplateException(msg)

        self._tpl_subj = next_line[len(subj_prefix):].strip()

        self._tpl_body = "\n".join(lines)

    def _load(self):
        if self._tpl_subj is None:
            with open_(self._path, 'r', encoding='utf-8') as f:
                self._load_lines(f.readlines())

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
