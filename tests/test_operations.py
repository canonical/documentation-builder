# Core modules
from copy import deepcopy
from os import path, remove
from unittest import TestCase
from shutil import rmtree

# Third party modules
import markdown
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


class TestOperations(TestCase):
    maxDiff = None

    def test_compile_metadata(self):
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

        self.assertEqual(root_metadata, {'site_title': 'root title'})
        self.assertEqual(
            child_metadata,
            {
                'site_title': 'child title',
                'navigation': [
                    {
                        'title': 'child page',
                        'location': 'index.md'
                    }
                ]
            }
        )
        self.assertEqual(
            child2_metadata,
            {
                'site_title': 'root title',
                'navigation': [{'title': 'child2 page'}]
            }
        )
        self.assertEqual(
            grandchild_metadata,
            {
                'site_title': 'grandchild title',
                'navigation': [
                    {
                        'title': 'child page',
                        'location': '../index.md'
                    }
                ]
            }
        )
        self.assertEqual(
            grandchild2_metadata,
            {
                'site_title': 'child title',
                'navigation': [
                    {
                        'title': 'grandchild2 page',
                        'location': '../../index.md'
                    }
                ]
            }
        )

    def test_copy_media(self):
        source_path = path.join(fixtures_path, 'copy_media', 'source_dir')
        relative_source_path = path.relpath(source_path)
        relative_source_path_2 = relative_source_path + '2'
        output_path = path.join(fixtures_path, 'copy_media', 'output_dir')
        relative_output_path = path.relpath(output_path)
        rmtree(output_path, ignore_errors=True)

        # Nonexistent directories should raise error
        with self.assertRaises(EnvironmentError):
            copy_media('non/existent/media', 'media')
        with self.assertRaises(EnvironmentError):
            copy_media('/non/existent/media', '/media')

        # The same directory should return False
        self.assertFalse(copy_media(source_path, source_path))
        self.assertFalse(
            copy_media(relative_source_path, './' + relative_source_path)
        )

        # We should be able to copy files
        self.assertTrue(copy_media(source_path, output_path))
        self.assertTrue(path.isfile(path.join(output_path, 'medium.png')))
        self.assertTrue(
            path.isfile(path.join(output_path, 'subfolder', 'medium.png'))
        )
        self.assertTrue(
            path.isfile(path.join(output_path, 'subfolder', 'medium2.png'))
        )

        # We should be able to overwrite files, and add new ones
        self.assertTrue(
            copy_media(relative_source_path_2, relative_output_path)
        )
        self.assertTrue(path.isfile(path.join(output_path, 'medium2.png')))
        self.assertTrue(
            path.isfile(path.join(output_path, 'subfolder', 'medium2.png'))
        )

    def test_find_files(self):
        source_dir = path.join(fixtures_path, 'find_files', 'source_dir')
        output_dir = path.join(fixtures_path, 'find_files', 'output_dir')

        files = find_files(source_dir, output_dir, {})

        # Check it categorieses each file in the fixtures correctly
        new_files = files[0]
        modified_files = files[1]
        unmodified_files = files[2]
        uppercase_files = files[3]

        self.assertEqual(
            new_files,
            [path.join(source_dir, 'subdir', 'new-file.md')]
        )
        self.assertEqual(
            modified_files,
            [path.join(source_dir, 'subdir', 'modified_file.md')]
        )
        self.assertEqual(
            unmodified_files,
            [
                path.join(source_dir, 'unchanged.md'),
                path.join(source_dir, 'subdir', 'unchanged.md')
            ]
        )
        self.assertEqual(
            uppercase_files,
            [path.join(source_dir, 'subdir', 'README.md')]
        )

        # Check it honours newer metadata
        files = find_files(
            source_dir,
            output_dir,
            {'.': {'modified': 2000000000, 'content': {}}}
        )

        new_files = files[0]
        modified_files = files[1]
        unmodified_files = files[2]
        uppercase_files = files[3]

        self.assertEqual(
            new_files,
            [path.join(source_dir, 'subdir', 'new-file.md')]
        )
        self.assertEqual(
            modified_files,
            [
                path.join(source_dir, 'unchanged.md'),
                path.join(source_dir, 'subdir', 'modified_file.md'),
                path.join(source_dir, 'subdir', 'unchanged.md')
            ]
        )
        self.assertEqual(
            unmodified_files,
            []
        )
        self.assertEqual(
            uppercase_files,
            [path.join(source_dir, 'subdir', 'README.md')]
        )

        # Check it honours newer metadata
        files = find_files(
            source_dir,
            output_dir,
            {'subdir': {'modified': 2000000000, 'content': {}}}
        )

        new_files = files[0]
        modified_files = files[1]
        unmodified_files = files[2]
        uppercase_files = files[3]

        self.assertEqual(
            new_files,
            [path.join(source_dir, 'subdir', 'new-file.md')]
        )
        self.assertEqual(
            modified_files,
            [
                path.join(source_dir, 'subdir', 'modified_file.md'),
                path.join(source_dir, 'subdir', 'unchanged.md')
            ]
        )
        self.assertEqual(
            unmodified_files,
            [path.join(source_dir, 'unchanged.md')]
        )
        self.assertEqual(
            uppercase_files,
            [path.join(source_dir, 'subdir', 'README.md')]
        )

    def test_find_metadata(self):
        source_dir = path.join(fixtures_path, 'find_metadata', 'source_dir')
        empty_dir = path.join(fixtures_path, 'find_metadata', 'empty_dir')

        metadata_items = find_metadata(source_dir)

        child2 = metadata_items['child2']

        # Should find all 4 metadata items
        self.assertEqual(len(metadata_items.keys()), 4)
        self.assertTrue(bool(metadata_items['.']))
        self.assertTrue(bool(child2))
        self.assertTrue(bool(metadata_items['child/grandchild']))
        self.assertEqual(
            child2['content']['navigation'][0]['children'][0]['title'],
            'A child'
        )

        # Should error if no metadata found
        with self.assertRaises(EnvironmentError):
            find_metadata(empty_dir)

    def test_parse_markdown(self):
        filepath = path.join(
            fixtures_path,
            'parse_markdown',
            'markdown.md'
        )
        html_filepath = path.join(
            fixtures_path,
            'parse_markdown',
            'markdown.html'
        )
        metadata = {'site_title': 'My site'}
        template_path = path.join(
            fixtures_path,
            'parse_markdown',
            'template.jinja2'
        )
        parser = markdown.Markdown()
        with open(template_path, encoding="utf-8") as template_file:
            template = Template(template_file.read())

        html = parse_markdown(parser, template, filepath, metadata)

        with open(html_filepath, encoding="utf-8") as html_file:
            example_html = html_file.read()
            self.assertEqual(html, example_html)

    def test_prepare_branches(self):
        repo = path.join(fixtures_path, 'prepare_branches', 'repo')
        not_repo = path.join(fixtures_path, 'prepare_branches', 'not_repo')
        output_path = '/output/path'
        no_versions = path.join(
            fixtures_path, 'prepare_branches', 'no_versions'
        )
        missing_branch = path.join(
            fixtures_path, 'prepare_branches', 'missing_branch'
        )

        # Error if provided an erroneous base directory
        with self.assertRaises(FileNotFoundError):
            prepare_branches("some/directory", output_path)

        # Error if asked to build branches with no versions file
        with self.assertRaises(FileNotFoundError):
            prepare_branches(no_versions, output_path, versions=True)

        # Error if asked to build branches with no git repository
        with self.assertRaises(GitCommandError):
            prepare_branches(not_repo, output_path, versions=True)

        # Error if asked to build branches with one of the branches missing
        with self.assertRaises(GitCommandError):
            prepare_branches(missing_branch, output_path, versions=True)

        # When not building versions, all existing directories should work
        self.assertEqual(
            prepare_branches(repo, output_path),
            [(repo, output_path)]
        )
        self.assertEqual(
            prepare_branches(not_repo, output_path),
            [(not_repo, output_path)]
        )
        self.assertEqual(
            prepare_branches(no_versions, output_path),
            [(no_versions, output_path)]
        )

        # Successfully builds version branches into temp directories
        branch_paths = prepare_branches(repo, output_path, versions=True)
        self.assertEqual(len(branch_paths), 2)
        for (branch_path, branch_output) in branch_paths:
            self.assertTrue(
                path.isfile(path.join(branch_path, 'metadata.yaml'))
            )
            self.assertTrue(branch_path.startswith('/tmp/'))
            self.assertTrue(branch_output.startswith(output_path))

    def test_relativize_paths(self):
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

        self.assertEqual(
            single_nested_paths_dictionary,
            {
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
        )

        double_nested_paths_dictionary = relativize_paths(
            deepcopy(example_dictionary),
            original_base_path='',
            new_base_path='en/nested'
        )

        self.assertEqual(
            double_nested_paths_dictionary,
            {
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
        )

        different_paths_dictionary = relativize_paths(
            deepcopy(example_dictionary),
            original_base_path='/fr/',
            new_base_path='/en/'
        )

        self.assertEqual(
            different_paths_dictionary,
            {
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
        )

    def test_replace_internal_links(self):
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
        self.assertEqual(
            replace_internal_links(input_html),
            expected_output_extensions
        )
        self.assertEqual(
            replace_internal_links(input_html, extensions=False),
            expected_output_no_extensions
        )

    def test_replace_media_links(self):
        html = (
            '\n\n<a href="/media/thing.png">some ../media</a>\n'
            '\n\n<a href="../media/image.png">link</a>\n'
        )

        # Relative links work
        self.assertEqual(
            replace_media_links(html, 'media', 'static', 'en'),
            (
                '\n\n<a href="/media/thing.png">some ../media</a>\n'
                '\n\n<a href="../static/image.png">link</a>\n'
            )
        )

        # Absolute links work
        self.assertEqual(
            replace_media_links(html, 'media', '/static', 'en'),
            (
                '\n\n<a href="/media/thing.png">some ../media</a>\n'
                '\n\n<a href="/static/image.png">link</a>\n'
            )
        )

    def test_write_html(self):
        html_content = "<html>\n<body>\n<h1>Hello</h1>\n<body>\n</html>"
        html_dir = path.join(
            fixtures_path,
            'write_html',
            'subdir'
        )
        html_filepath = path.join(html_dir, 'file.html')

        # Make sure it doesn't exist already
        if path.exists(html_dir):
            rmtree(html_dir)

        write_html(html_content, html_filepath)

        self.assertTrue(path.isfile(html_filepath))
        with open(html_filepath, encoding="utf-8") as html_file:
            self.assertEqual(html_file.read(), html_content)

        # Delete it again
        rmtree(html_dir)
