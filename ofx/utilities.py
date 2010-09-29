import os.path
import re

def _(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path

acct_re = re.compile(r'([\w.\-/]{1,22})')
#bankaccts_re = re.compile(r'\(([\w.\-/]{1,9}),\s*([\w.\-/]{1,22})\)')
pair_re = re.compile(r'\(([\w.\-/]{1,22}),\s*([\w.\-/]{1,22})\)')
naked_re = re.compile(r'(\b)([\w.\-/]{1,22})')

def parse_accts(string):
    """ WRITEME """
    # FIXME - it would be nice to be able to mix&match the
    # two styles within a single line.
    return pair_re.findall(string) or naked_re.findall(string)