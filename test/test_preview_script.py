
import os.path
from subprocess import CalledProcessError, check_output, STDOUT

from .tests_helpers import root, assert_template_path

def test_script():
    script = os.path.join(root(), 'preview')
    template = assert_template_path('template-1')

    preview = None

    try:
        preview = check_output([script, template], stderr=STDOUT).decode('utf-8')
    except CalledProcessError as cpe:
        print(cpe.output)
        raise

    assert 'error' not in preview.lower(), "Should not have errored"
    assert 'Body' in preview, "Should have output the body"
