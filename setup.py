import sys
from setuptools import setup

# The importer relies heavily on glob recursive search capability.
# This was only introduced in Python 3.5:
# https://docs.python.org/3.6/whatsnew/3.5.html#glob
assert sys.version_info >= (3, 5), (
    "The documentation importer requires Python 3.5 or newer"
)

setup(
    name='ubuntudesign.documentation-builder',
    version='0.2.1',
    author='Canonical webteam',
    author_email='robin+pypi@canonical.com',
    url='https://github.com/ubuntudesign/documentation-builder',
    packages=[
        'ubuntudesign.documentation_builder',
    ],
    description=(
        'A command-line tool for building documentation from repositories '
        'into HTML files. Initially based on '
        'https://github.com/juju/docs/blob/master/tools/mdbuild.py.'
    ),
    scripts=['bin/documentation-builder'],
    long_description=open('README.md').read(),
    install_requires=[
        "Markdown>=2.6.6",
        "GitPython>=2.0.8",
        "mdx-anchors-away>=1.0.1",
        "mdx-callouts>=1.0.0",
        "mdx-foldouts>=1.0.0"
    ],
)
