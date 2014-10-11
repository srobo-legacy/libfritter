
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
