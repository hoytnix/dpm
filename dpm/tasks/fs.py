import os


def working_directory(path=None):
    home = os.path.expanduser('~')
    if path:
        return os.path.join(home, path)
    else:
        return home


def local_directory(path=None):
    local = working_directory(path='.local/share/dpm')
    if path:
        return os.path.join(local, path)
    else:
        return local
