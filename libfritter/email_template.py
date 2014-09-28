
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
    def __init__(self, template_id):
        """Create a new template around the given id.

        Parameters
        ----------
        template_id : str
            Will be passed to the `load_lines` method to load the raw
            content of the template.
            The default implementation expects this to be a path.
        """

        self._tpl_id = template_id
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

            self._tpl_to = next_line[len(to_prefix):].strip()
            next_line = lines.pop(0)

        if not next_line.startswith(subj_prefix):
            msg = "Template must contain a subject within its first two lines."
            raise InvalidTemplateException(msg)

        self._tpl_subj = next_line[len(subj_prefix):].strip()

        stripped_lines = [l.rstrip() for l in lines]
        self._tpl_body = newline.join(stripped_lines).strip(newline)

    def _load(self):
        if self._tpl_subj is None:
            self._process_lines(self.load_lines(self._tpl_id))

    def load_lines(self, template_id):
        """Load the template content.
        The default implementation loads from a file on disk.

        Parameters
        ----------
        template_id : str
            The value given to the instance when created

        Returns
        -------
        list
            The lines which make up the template. It doesn't matter whether
            they include the trailing newlines or not.
        """
        with open_(template_id, 'r', encoding='utf-8') as f:
            return f.readlines()

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
