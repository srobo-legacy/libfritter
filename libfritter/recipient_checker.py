
from .previewer import BadRecipient, MissingRecipient

class RecipientChecker(object):
    def no_recipient(self):
        """Called when there are no recipients. If this is valid, then
        the method need not do anything. If this is not valid, then it
        should raise ``MissingRecipient`` ideally with some comment about
        would be valid.
        """
        pass

    def describe(self, recipient):
        """Will be passed in turn each of the values from the "To:" line
        of the template, should return a description of the recipient or
        raise ``BadRecipient``.

        Parameters
        ----------
        recipient : str
            One of the values from the "To:" line of the template.

        Returns
        -------
        str
            A description of the recipient. The value returned will be
            shown in the preview, even if it is empty. Thus, if there is
            no description available this should just return the input value.
        """
        return recipient

class InvalidRecipient(BadRecipient):
    def __init__(self, recipient, valid_recipients):
        valid_str = "', '".join(valid_recipients)
        super(InvalidRecipient, self).__init__(recipient, \
            "Invalid recipient '{{0}}', expecting one of '{0}'.".format(valid_str)
        )

class RestrictedRecipientsChecker(object):
    def __init__(self, valid_recipients):
        """Create a checker which only allows recipients within a given lists.
        Note: the members of the valid list will be included in any
        exceptions that this class throws.

        Parameters
        ----------
        valid_recipients : list of str
            A list of names which are valid for use in templates.
        """
        self._valid_recipients = set(valid_recipients)

    def check_valid(self, recipient):
        if not recipient in self._valid_recipients:
            raise InvalidRecipient(recipient, self._valid_recipients)

    def no_recipient(self):
        valid_str = "', '".join(self._valid_recipients)
        raise MissingRecipient("Expecting one of '{0}'.".format(valid_str))

    def describe(self, recipient):
        self.check_valid(recipient)
        return recipient
