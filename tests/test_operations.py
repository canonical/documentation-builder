# Core modules
from copy import deepcopy
from os import path
from unittest import TestCase
from shutil import rmtree

# Local modules
from ubuntudesign.documentation_builder.operations import (
    relativize_paths,
    copy_media,
    replace_media_links
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

    def test_relativize_paths_1(self):
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


    # def test_replace_media_paths(self):
    #     mock_builder = mock.Mock()
    #     mock_builder.source_media_path = '/original/media'
    #     mock_builder.output_media_path = '/new/static/media'
    #     mock_builder.media_url = None
    #
    #     output_content = Builder._replace_media_links(
    #         self=mock_builder,
    #         content='<img src="media/image.jpg" />',
    #         source_filepath='/original/index.md',
    #         output_filepath='/new/index.html'
    #     )
    #
    #     self.assertEqual(
    #         output_content,
    #         '<img src="static/media/image.jpg" />'
    #     )
