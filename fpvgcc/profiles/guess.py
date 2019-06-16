

import re


def guess_profile(fpath):
    fp = open(fpath, "rb")
    fp.seek(-300 - 1, 2)

    rex = r"^OUTPUT\((?P<file>[\S]+)\s(?P<sig>[\S]+)\)$"
    line = fp.readlines()[-1].strip().decode()

    matches = re.search(rex, line)
    if matches:
        return matches.group('sig')
    return 'default'
