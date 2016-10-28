# Core modules
from copy import deepcopy
from os import path, utime
from shutil import rmtree

# Third party modules
import markdown
import pytest
from git import Repo
from git.exc import GitCommandError
from jinja2 import Template

# Local modules
from ubuntudesign.documentation_builder.operations import (
    compile_metadata,
    copy_media,
    find_files,
    find_metadata,
    parse_markdown,
    prepare_branches,
    relativize_paths,
    replace_internal_links,
    replace_media_links,
    write_html
)
from ubuntudesign.documentation_builder.builder import markdown_extensions


example_dictionary = {
    'location': '/base/file1.md',
    'title': 'A page about fish.md',
    'children': [
        {
            'title': 'Some nested file',
            'location': 'file2.md'
        },
        {
            'title': 'Some nested file',
            'location': '../en/nested/file3.md'
        }
    ]
}


fixtures_path = path.join(path.dirname(__file__), 'fixtures')


def test_compile_metadata():
    metadata_items = {
        '.': {
            'content': {'site_title': 'root title'}
        },
        'child': {
            'content': {
                'site_title': 'child title',
                'navigation': [
                    {
                        'title': 'child page',
                        'location': 'index.md'
                    }
                ]
            }
        },
        'child2': {
            'content': {
                'navigation': [{'title': 'child2 page'}]
            }
        },
        './child/grandchild': {
            'content': {
                'site_title': 'grandchild title'
            }
        },
        './child/grandchild2': {
            'content': {
                'navigation': [
                    {
                        'title': 'grandchild2 page',
                        'location': '/index.md'
                    }
                ]
            }
        }
    }

    root_metadata = compile_metadata(metadata_items, '.')
    child_metadata = compile_metadata(metadata_items, './child')
    child2_metadata = compile_metadata(metadata_items, 'child2')
    grandchild_metadata = compile_metadata(
        metadata_items,
        'child/grandchild'
    )
    grandchild2_metadata = compile_metadata(
        metadata_items,
        './child/grandchild2'
    )

    expected_child_metadata = {
        'site_title': 'child title',
        'navigation': [
            {
                'title': 'child page',
                'location': 'index.md'
            }
        ]
    }
    expected_child2_metadata = {
        'site_title': 'root title',
        'navigation': [{'title': 'child2 page'}]
    }
    expected_grandchild_metadata = {
        'site_title': 'grandchild title',
        'navigation': [
            {
                'title': 'child page',
                'location': '../index.md'
            }
        ]
    }
    expected_grandchild2_metadata = {
        'site_title': 'child title',
        'navigation': [
            {
                'title': 'grandchild2 page',
                'location': '../../index.md'
            }
        ]
    }

    assert root_metadata == {'site_title': 'root title'}
    assert child_metadata == expected_child_metadata
    assert child2_metadata == expected_child2_metadata
    assert grandchild_metadata == expected_grandchild_metadata
    assert grandchild2_metadata == expected_grandchild2_metadata


def test_copy_media():
    source_path = path.join(fixtures_path, 'copy_media', 'source_dir')
    relative_source_path = path.relpath(source_path)
    relative_source_path_2 = relative_source_path + '2'
    output_path = path.join(fixtures_path, 'copy_media', 'output_dir')
    relative_output_path = path.relpath(output_path)
    rmtree(output_path, ignore_errors=True)

    # Nonexistent directories should raise error
    with pytest.raises(EnvironmentError):
        copy_media('non/existent/media', 'media')
    with pytest.raises(EnvironmentError):
        copy_media('/non/existent/media', '/media')

    # The same directory should return False
    assert bool(copy_media(source_path, source_path)) is False
    assert bool(
        copy_media(relative_source_path, './' + relative_source_path)
    ) is False

    # We should be able to copy files
    assert copy_media(source_path, output_path) is True
    assert path.isfile(path.join(output_path, 'medium.png')) is True
    assert path.isfile(
        path.join(output_path, 'subfolder', 'medium.png')
    ) is True
    assert path.isfile(
        path.join(output_path, 'subfolder', 'medium2.png')
    ) is True

    # We should be able to overwrite files, and add new ones
    assert copy_media(relative_source_path_2, relative_output_path) is True
    assert path.isfile(path.join(output_path, 'medium2.png')) is True
    assert path.isfile(
        path.join(output_path, 'subfolder', 'medium2.png')
    ) is True


def test_find_files():
    source_dir = path.join(fixtures_path, 'find_files', 'source_dir')
    output_dir = path.join(fixtures_path, 'find_files', 'output_dir')

    paths = {
        'new_file': path.join(source_dir, 'subdir', 'new-file.md'),
        'readme': path.join(source_dir, 'subdir', 'README.md'),
        'unchanged_md': path.join(source_dir, 'unchanged.md'),
        'unchanged_html': path.join(output_dir, 'unchanged.html'),
        'unchanged_sub_md': path.join(
            source_dir, 'subdir', 'unchanged.md'
        ),
        'unchanged_sub_html': path.join(
            output_dir, 'subdir', 'unchanged.html'
        ),
        'modified_md': path.join(source_dir, 'subdir', 'modified_file.md'),
        'modified_html': path.join(
            output_dir, 'subdir', 'modified_file.html'
        )
    }

    # Set modified times
    old = 1000000000
    newish = 1500000000
    new = 2000000000
    utime(paths['unchanged_md'], (old, old))
    utime(paths['unchanged_html'], (newish, newish))
    utime(paths['unchanged_sub_md'], (old, old))
    utime(paths['unchanged_sub_html'], (newish, newish))
    utime(paths['modified_md'], (newish, newish))
    utime(paths['modified_html'], (old, old))

    files = find_files(source_dir, output_dir, {})

    # Check it categorieses each file in the fixtures correctly
    new_files = files[0]
    modified_files = files[1]
    unmodified_files = files[2]
    uppercase_files = files[3]

    assert new_files == [paths['new_file']]
    assert modified_files == [paths['modified_md']]
    assert unmodified_files == [
        paths['unchanged_md'], paths['unchanged_sub_md']
    ]
    assert uppercase_files == [paths['readme']]

    # Check it honours newer metadata
    files = find_files(
        source_dir,
        output_dir,
        {'.': {'modified': new, 'content': {}}}
    )

    new_files = files[0]
    modified_files = files[1]
    unmodified_files = files[2]
    uppercase_files = files[3]

    assert new_files == [paths['new_file']]
    assert modified_files == [
        paths['unchanged_md'],
        paths['modified_md'],
        paths['unchanged_sub_md']
    ]
    assert unmodified_files == []
    assert uppercase_files == [paths['readme']]

    # Check it honours newer metadata
    files = find_files(
        source_dir,
        output_dir,
        {'subdir': {'modified': new, 'content': {}}}
    )

    new_files = files[0]
    modified_files = files[1]
    unmodified_files = files[2]
    uppercase_files = files[3]

    assert new_files == [paths['new_file']]
    assert modified_files == [
        path.join(source_dir, 'subdir', 'modified_file.md'),
        path.join(source_dir, 'subdir', 'unchanged.md')
    ]
    assert unmodified_files == [paths['unchanged_md']]
    assert uppercase_files == [paths['readme']]


def test_find_metadata():
    source_dir = path.join(fixtures_path, 'find_metadata', 'source_dir')
    empty_dir = path.join(fixtures_path, 'find_metadata', 'empty_dir')

    metadata_items = find_metadata(source_dir)

    child2 = metadata_items['child2']

    # Should find all 4 metadata items
    assert len(metadata_items.keys()) == 4
    assert bool(metadata_items['.']) is True
    assert bool(child2) is True
    assert bool(metadata_items['child/grandchild']) is True
    nav_title = child2['content']['navigation'][0]['children'][0]['title']
    assert nav_title == 'A child'

    # Should error if no metadata found
    with pytest.raises(EnvironmentError):
        find_metadata(empty_dir)


def test_parse_markdown():
    function_fixtures = path.join(fixtures_path, 'parse_markdown')
    frontmatter_path = path.join(
        function_fixtures,
        'metadata_markdown_frontmatter.md'
    )
    mmdata_path = path.join(function_fixtures, 'metadata_markdown_mmdata.md')
    plain_path = path.join(function_fixtures, 'plain_markdown.md')
    # The "error" file tries to trigger an error with the frontmatter parser,
    # which should be handled gracefully
    plain_error_path = path.join(function_fixtures, 'plain_markdown_error.md')
    plain_output_path = path.join(function_fixtures, 'plain_markdown.html')
    metadata_output_path = path.join(
        function_fixtures, 'metadata_markdown.html'
    )

    metadata = {'site_title': 'A site'}
    template_path = path.join(function_fixtures, 'template.jinja2')
    parser = markdown.Markdown(markdown_extensions)
    with open(template_path, encoding="utf-8") as template_file:
        template = Template(template_file.read())

    frontmatter_html = parse_markdown(
        parser, template, frontmatter_path, metadata
    )
    mmdata_html = parse_markdown(parser, template, mmdata_path, metadata)
    plain_html = parse_markdown(parser, template, plain_path, metadata)
    plain_html_error = parse_markdown(
        parser, template, plain_error_path, metadata
    )

    with open(plain_output_path, encoding="utf-8") as plain_output_file:
        expected_plain_html = plain_output_file.read().strip()
        assert plain_html == expected_plain_html
        assert plain_html_error == expected_plain_html

    with open(metadata_output_path, encoding="utf-8") as metadata_output_file:
        expected_metadata_html = metadata_output_file.read().strip()
        assert frontmatter_html == expected_metadata_html
        assert mmdata_html == expected_metadata_html


def test_prepare_branches():
    repo_path = path.join(fixtures_path, 'prepare_branches', 'repo')
    not_repo = path.join(fixtures_path, 'prepare_branches', 'not_repo')

    # Clean up repository
    if path.exists(repo_path):
        rmtree(repo_path)

    # Clone repository and pull down all branches
    repo = Repo.clone_from(
        (
            "https://github.com/CanonicalLtd/"
            "documentation-builder-test-prepare-branches.git"
        ),
        repo_path
    )
    origin = repo.remotes.origin
    repo.create_head('no-versions', origin.refs['no-versions'])
    repo.create_head('missing-branch', origin.refs['missing-branch'])
    repo.create_head('1.0', origin.refs['1.0'])
    repo.create_head('latest', origin.refs['latest'])

    # Error if provided an erroneous base directory
    with pytest.raises(FileNotFoundError):
        prepare_branches("some/directory", 'output')

    # Error if asked to build branches with no git repository
    with pytest.raises(GitCommandError):
        prepare_branches(not_repo, 'output', versions=True)

    repo.heads['no-versions'].checkout()
    # Error if asked to build branches with no versions file
    with pytest.raises(FileNotFoundError):
        prepare_branches(repo_path, 'output', versions=True)

    repo.heads['missing-branch'].checkout()
    # Error if asked to build branches with one of the branches missing
    with pytest.raises(GitCommandError):
        prepare_branches(repo_path, 'output', versions=True)

    # When not building versions, all existing directories should work
    repo.heads['master'].checkout()
    assert prepare_branches(repo_path, 'output') == [(repo_path, 'output')]

    repo.heads['no-versions'].checkout()
    assert prepare_branches(repo_path, 'output') == [(repo_path, 'output')]

    repo.heads['missing-branch'].checkout()
    assert prepare_branches(repo_path, 'output') == [(repo_path, 'output')]

    assert prepare_branches(not_repo, 'output') == [(not_repo, 'output')]

    # Successfully builds version branches into temp directories
    repo.heads['master'].checkout()
    branch_paths = prepare_branches(repo_path, 'output', versions=True)

    assert len(branch_paths) == 2

    for (branch_path, branch_output) in branch_paths:
        assert path.isfile(path.join(branch_path, 'metadata.yaml')) is True
        assert branch_path.startswith('/tmp/') is True
        assert branch_output.startswith('output') is True

    rmtree(repo_path)


def test_relativize_paths():
    example_dictionary = {
        'location': '/base/file1.md',
        'title': 'A page about fish.md',
        'children': [
            {
                'title': 'Some nested file',
                'location': 'file2.md'
            },
            {
                'title': 'Some nested file',
                'location': '../en/nested/file3.md'
            }
        ]
    }

    single_nested_paths_dictionary = relativize_paths(
        deepcopy(example_dictionary),
        original_base_path='en',
        new_base_path='en/nested'
    )
    expected_single_nested_paths_dict = {
        'location': '../../base/file1.md',
        'title': 'A page about fish.md',
        'children': [
            {
                'title': 'Some nested file',
                'location': '../file2.md'
            },
            {
                'title': 'Some nested file',
                'location': 'file3.md'
            }
        ]
    }

    assert single_nested_paths_dictionary == expected_single_nested_paths_dict

    double_nested_paths_dictionary = relativize_paths(
        deepcopy(example_dictionary),
        original_base_path='',
        new_base_path='en/nested'
    )
    expected_double_nested_paths_dict = {
        'location': '../../base/file1.md',
        'title': 'A page about fish.md',
        'children': [
            {
                'title': 'Some nested file',
                'location': '../../file2.md'
            },
            {
                'title': 'Some nested file',
                'location': 'file3.md'
            }
        ]
    }

    assert double_nested_paths_dictionary == expected_double_nested_paths_dict

    different_paths_dictionary = relativize_paths(
        deepcopy(example_dictionary),
        original_base_path='/fr/',
        new_base_path='/en/'
    )
    expected_different_paths_dict = {
        'location': '../base/file1.md',
        'title': 'A page about fish.md',
        'children': [
            {
                'title': 'Some nested file',
                'location': '../fr/file2.md'
            },
            {
                'title': 'Some nested file',
                'location': 'nested/file3.md'
            }
        ]
    }

    assert different_paths_dictionary == expected_different_paths_dict


def test_replace_internal_links():
    input_html = (
        '<html>\n'
        '<body>\n'
        '<a href="page1.md">page1.md</a>\n'
        '<a href="../page2.md">../page2.md</a>\n'
        '<a href="subfolder/page3.md">subfolder/page3.md</a>\n'
        '<a href="/index.md">index.md</a>\n'
        '<a href="http://example.com/index.md">index.md</a>\n'
        '</body>\n'
        '</html>'
    )
    output_extensions = replace_internal_links(input_html)
    expected_output_extensions = (
        '<html>\n'
        '<body>\n'
        '<a href="page1.html">page1.md</a>\n'
        '<a href="../page2.html">../page2.md</a>\n'
        '<a href="subfolder/page3.html">subfolder/page3.md</a>\n'
        '<a href="/index.md">index.md</a>\n'
        '<a href="http://example.com/index.md">index.md</a>\n'
        '</body>\n'
        '</html>'
    )
    assert output_extensions == expected_output_extensions

    output_no_extensions = replace_internal_links(input_html, extensions=False)
    expected_output_no_extensions = (
        '<html>\n'
        '<body>\n'
        '<a href="page1">page1.md</a>\n'
        '<a href="../page2">../page2.md</a>\n'
        '<a href="subfolder/page3">subfolder/page3.md</a>\n'
        '<a href="/index.md">index.md</a>\n'
        '<a href="http://example.com/index.md">index.md</a>\n'
        '</body>\n'
        '</html>'
    )
    assert output_no_extensions == expected_output_no_extensions


def test_replace_media_links():
    html = (
        '\n\n<a href="/media/thing.png">some ../media</a>\n'
        '\n\n<a href="../media/image.png">link</a>\n'
    )

    # Relative links work
    output_relative = replace_media_links(html, 'media', 'static', 'en')
    expected_output_relative = (
        '\n\n<a href="/media/thing.png">some ../media</a>\n'
        '\n\n<a href="../static/image.png">link</a>\n'
    )
    assert output_relative == expected_output_relative

    # Absolute links work
    output_absolute = replace_media_links(html, 'media', '/static', 'en')
    expected_output_absolute = (
        '\n\n<a href="/media/thing.png">some ../media</a>\n'
        '\n\n<a href="/static/image.png">link</a>\n'
    )
    assert output_absolute == expected_output_absolute


def test_write_html():
    html_content = "<html>\n<body>\n<h1>Hello</h1>\n<body>\n</html>"
    html_dir = path.join(
        fixtures_path,
        'write_html',
        'subdir'
    )
    md_filepath = path.join(html_dir, 'file.md')
    html_filepath = path.join(html_dir, 'file.html')

    # Make sure it doesn't exist already
    if path.exists(html_dir):
        rmtree(html_dir)

    written_filepath = write_html(html_content, md_filepath)

    assert written_filepath == html_filepath
    assert path.isfile(html_filepath) is True
    with open(html_filepath, encoding="utf-8") as html_file:
        assert html_file.read() == html_content

    # Delete it again
    rmtree(html_dir)
