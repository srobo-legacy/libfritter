
from .email_template import EmailTemplate
from .template_source import FileTemaplateSource

class FileTemplateFactory(object):
    """A simple wrapper around ``FileTemaplateSource`` and ``EmailTemplate``
    whose ``load`` method is suitable for passing to the ``Mailer`` or
    ``Previewer`` classes.
    """
    def __init__(self, root):
        self._source = FileTemaplateSource(root)

    def load(self, name):
        """Method which actually loads the template given a name

        Parameters
        ----------
        name : str
            The name of the template to load.

        Returns
        -------
        EmailTemplate
            A constructed template instance.
        """
        raw_template = self._source.load(name)
        et = EmailTemplate(raw_template)
        return et
