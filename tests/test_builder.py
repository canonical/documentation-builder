from unittest import mock, TestCase
from copy import deepcopy
from ubuntudesign.documentation_builder.builder import (
    Builder,
    relativize_paths
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


class TestDocumentationBuilder(TestCase):
    maxDiff = None

    def test_relativize_paths_1(self):
        updated_dictionary = relativize_paths(
            deepcopy(example_dictionary),
            original_base_path='',
            new_base_path='en/nested'
        )

        expected_dictionary = deepcopy(example_dictionary)
        expected_dictionary['location'] = '../../base/file1.md'
        expected_dictionary['children'][0]['location'] = '../../file2.md'
        expected_dictionary['children'][1]['location'] = 'file3.md'

        self.assertEqual(updated_dictionary, expected_dictionary)

    def test_relativize_paths_2(self):
        updated_dictionary = relativize_paths(
            deepcopy(example_dictionary),
            original_base_path='en',
            new_base_path='en/nested'
        )

        expected_dictionary = deepcopy(example_dictionary)
        expected_dictionary['location'] = '../../base/file1.md'
        expected_dictionary['children'][0]['location'] = '../file2.md'
        expected_dictionary['children'][1]['location'] = 'file3.md'

        self.assertEqual(updated_dictionary, expected_dictionary)

    def test_relativize_paths_3(self):
        updated_dictionary = relativize_paths(
            deepcopy(example_dictionary),
            original_base_path='/fr/',
            new_base_path='/en/'
        )

        expected_dictionary = deepcopy(example_dictionary)
        expected_dictionary['location'] = '../base/file1.md'
        expected_dictionary['children'][0]['location'] = '../fr/file2.md'
        expected_dictionary['children'][1]['location'] = 'nested/file3.md'

        self.assertEqual(updated_dictionary, expected_dictionary)

    def test_replace_media_paths(self):
        mock_builder = mock.Mock()
        mock_builder.source_media_path = '/original/media'
        mock_builder.output_media_path = '/new/static/media'
        mock_builder.media_url = None

        output_content = Builder._replace_media_links(
            self=mock_builder,
            content='<img src="media/image.jpg" />',
            source_filepath='/original/index.md',
            output_filepath='/new/index.html'
        )

        self.assertEqual(
            output_content,
            '<img src="static/media/image.jpg" />'
        )
