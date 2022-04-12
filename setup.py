#! /usr/bin/env python3

# Core
import sys
from setuptools import setup

# The importer relies heavily on glob recursive search capability.
# This was only introduced in Python 3.5:
# https://docs.python.org/3.6/whatsnew/3.5.html#glob
assert sys.version_info >= (
    3,
    5,
), "The documentation importer requires Python 3.5 or newer"

setup(
    name="ubuntudesign.documentation-builder",
    version="1.6.6",
    author="Canonical webteam",
    author_email="robin+pypi@canonical.com",
    url="https://github.com/ubuntudesign/documentation-builder",
    packages=[
        "ubuntudesign.documentation_builder",
    ],
    package_data={"ubuntudesign.documentation_builder": ["resources/*"]},
    description=(
        "A command-line tool for building documentation from repositories "
        "into HTML files. Initially based on "
        "https://github.com/juju/docs/blob/master/tools/mdbuild.py."
    ),
    long_description=open("README.rst").read(),
    install_requires=[
        "GitPython==3.1.27",
        "Jinja2==2.11.3",
        "Markdown==2.6.6",
        "mdx-anchors-away==1.0.1",
        "mdx-foldouts==1.0.0",
        "python-frontmatter==0.2.1",
        "pygments==2.4.0",
        "PyYAML==6.0",
        "beautifulsoup4==4.10.0",
        "markdown_urlize==0.2.0",
    ],
    setup_requires=["pytest-runner"],
    tests_require=[
        "mock==2.0.0",
        "nose==1.3.7",
        "pytest==3.0.2",
        "pytest-cov==2.4.0",
    ],
    scripts=["documentation-builder"],
)
