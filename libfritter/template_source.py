
import os.path
import sys

if sys.version_info[0] < 3:
    import codecs
    open_ = codecs.open
else:
    open_ = open

class FileTemaplateSource(object):
    "A source of template contents based on .txt files"

    extension = '.txt'

    def __init__(self, root):
        self._root = root

    def load(self, name):
        path = os.path.join(self._root, name + self.extension)
        with open_(path, 'r', encoding='utf-8') as f:
            return f.read()
