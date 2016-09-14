from setuptools import setup

setup(
    name='ubuntudesign.documentation-builder',
    version='0.0.2',
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
    # long_description=open('README.md').read(),
    install_requires=["Markdown>=2.6.0"],
)

