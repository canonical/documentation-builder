#! /usr/bin/env python3

# Core
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
    version='1.3.1',
    author='Canonical webteam',
    author_email='robin+pypi@canonical.com',
    url='https://github.com/ubuntudesign/documentation-builder',
    packages=[
        'ubuntudesign.documentation_builder',
    ],
    package_data={
        'ubuntudesign.documentation_builder': ['resources/*']
    },
    description=(
        'A command-line tool for building documentation from repositories '
        'into HTML files. Initially based on '
        'https://github.com/juju/docs/blob/master/tools/mdbuild.py.'
    ),
    long_description=open('README.rst').read(),
    install_requires=[
        "GitPython==2.0.8",
        "Jinja2==2.8",
        "Markdown==2.6.6",
        "mdx-anchors-away==1.0.1",
        "mdx-callouts==1.0.0",
        "mdx-foldouts==1.0.0",
        "python-frontmatter==0.2.1",
        "pygments==2.2.0",
        "PyYAML==3.12",
        "beautifulsoup4==4.5.1",
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        "mock==2.0.0",
        "nose==1.3.7",
        "pytest==3.0.2",
        "pytest-cov==2.4.0",
    ],
)
