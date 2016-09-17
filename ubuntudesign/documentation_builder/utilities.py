from os import listdir, makedirs, path, stat
from shutil import copytree, copy2


def mergetree(src, dst, symlinks=False, ignore=None):
    if not path.exists(dst):
        makedirs(dst)
    for item in listdir(src):
        source = path.join(src, item)
        destination = path.join(dst, item)
        if path.isdir(source):
            copytree(source, destination, symlinks, ignore)
        else:
            if (
                not path.exists(destination) or
                stat(source).st_mtime - stat(destination).st_mtime > 1
            ):
                copy2(source, destination)
