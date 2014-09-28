
import os.path
from subprocess import CalledProcessError, check_output, STDOUT

from .tests_helpers import root, assert_template_path

def get_preview(name):
    script = os.path.join(root(), 'preview')
    template = assert_template_path(name)

    preview = None

    try:
        preview = check_output([script, template], stderr=STDOUT).decode('utf-8')
    except CalledProcessError as cpe:
        print(cpe.output)
        raise

    return preview

def test_valid_template():
    preview = get_preview('template-1')

    assert 'error' not in preview.lower(), "Should not have errored"
    assert 'Body' in preview, "Should have output the body"

def test_invalid_template():
    preview = get_preview('invalid-1')

    assert 'Error' in preview, "Should have output an error"
    assert 'has no subject line' in preview, "Should have output a description of the errors"
    assert 'Body' not in preview, "Should not output the body when template invalid"
