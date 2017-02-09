# System
from shutil import rmtree

# Local modules
from ubuntudesign.documentation_builder.cli import main, parse_arguments


def test_parse_arguments():
    arguments = parse_arguments([])

    assert type(arguments) == dict

def test_main():
    main(
        [
             '--base-directory',
             'tests/fixtures/builder/base/',
             '--output-path',
             'doesnt/matter'
        ]
    )
    rmtree('doesnt')

