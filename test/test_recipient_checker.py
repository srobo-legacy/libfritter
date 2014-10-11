
from ..libfritter.previewer import MissingRecipient
from ..libfritter.recipient_checker import RestrictedRecipientsChecker, \
                                           InvalidRecipient

def get_checker(recipients):
    return RestrictedRecipientsChecker(recipients)

def test_valid():
    to = 'abc'
    rrc = get_checker([to])
    actual = rrc.describe(to)
    assert to == actual, "Wrong description"

def test_invalid():
    to = 'abc'
    valid = 'def'
    rrc = get_checker([valid])
    threw = False
    try:
        rrc.describe(to)
    except InvalidRecipient as ir:
        threw = True
        assert to == ir.recipient, "Didn't mention the recipient"
        msg = str(ir)
        assert valid in msg, "Didn't mention what the valid values would be"

    assert threw, "Failed to reject invalid recipient"

def test_no_recipient():
    valid = 'def'
    rrc = get_checker([valid])
    threw = False
    try:
        rrc.no_recipient()
    except MissingRecipient as mr:
        threw = True
        msg = str(mr)
        assert valid in msg, "Didn't mention what the valid values would be"

    assert threw, "Failed to require a recipient"
