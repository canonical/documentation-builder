# Core modules
import re
from os import environ, listdir, makedirs, path, stat
from shutil import copy2


def mergetree(src, dst, symlinks=False, ignore=None):
    """
    Deep-merge two directory trees, overwriting changed files
    """

    if not path.isdir(src):
        raise EnvironmentError('Source tree not found: ' + src)

    makedirs(dst, exist_ok=True)
    for item in listdir(src):
        source = path.join(src, item)
        destination = path.join(dst, item)
        if path.isdir(source):
            mergetree(source, destination, symlinks, ignore)
        else:
            if (
                not path.exists(destination) or
                stat(source).st_mtime - stat(destination).st_mtime > 1
            ):
                copy2(source, destination)


def relativize(location, original_base_path, new_base_path):
    """
    Update a relative path for a new base location
    """

    if location.startswith('/'):
        abs_location = location.rstrip('/')
    else:
        abs_location = '/' + path.join(original_base_path, location).strip('/')
    abs_dirpath = '/' + new_base_path

    return path.relpath(abs_location, abs_dirpath)


def replace_link_paths(html, old_link_path, new_link_path):
    """
    In some HTML text, replace old link paths with a new path
    """

    link_search = r'((?<=src=["\'])|(?<=href=["\'])){}(?=/)'.format(
        old_link_path.replace('.', '\.')
    )

    return re.sub(link_search, new_link_path, html)


def matching_metadata(metadata_items, context_path):
    """
    Given a list of metadata items and a directory path,
    return only the items which relate to that path
    """

    for dirpath, item in sorted(
        metadata_items.items(), key=sort_paths
    ):
        if '..' not in path.relpath(context_path, dirpath):
            yield (dirpath, item)


def sort_paths(item):
    """
    Sort key for metadata items to normalise paths
    """

    return path.normpath(item[0])


def cache_dir(name):
    """
    Return the path to a named user cache directory (e.g. ~/.cache/name).
    Create the directory if it doesn't exist
    """

    cache_dir = environ.get(
        'XDG_CACHE_HOME',
        path.join(path.expanduser('~'), '.cache')
    )
    named_cache = path.join(cache_dir, name)

    if not path.isdir(named_cache):
        makedirs(named_cache)

    return named_cache
