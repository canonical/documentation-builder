# Core modules
from glob import iglob
from os import makedirs, path
from tempfile import TemporaryDirectory

# Third party modules
import markdown
from git import Repo

# Local modules
from .utilities import mergetree

# Configuration
# ==
default_title = 'Juju Documentation'
markdown_extensions = [
    'markdown.extensions.meta',
    'markdown.extensions.tables',
    'markdown.extensions.fenced_code',
    'markdown.extensions.def_list',
    'markdown.extensions.attr_list',
    'markdown.extensions.toc',
    'callouts',
    'anchors_away',
    'foldouts'
]


def parse_file(filepath):
    """
    Parse an individual markdown file to HTML, also returning
    the meta title
    """

    with open(filepath) as markdown_file:
        parser = markdown.Markdown(extensions=markdown_extensions)

        html_content = parser.convert(markdown_file.read())
        title = default_title

        if hasattr(parser, 'Meta') and 'title' in parser.Meta:
            title = parser.Meta['title'][0]

    return (title, html_content)


def parse_template(template, contents, title, navigation):
    """
    Given a template string with `%%CONTENT%%`, '%%TITLE%%' and '%%DOCNAV%%'
    placeholders, add content, title and navigation.
    """

    html_document = template

    replace = [
        ('%%TITLE%%', title),
        ('%%CONTENT%%', contents),
        ('%%DOCNAV%%', navigation)
    ]

    for (original, replacement) in replace:
        html_document = html_document.replace(original, replacement)

    return html_document


def parse_files(
    source_path,
    destination_path,
    template,
    navigation,
    media_path,
    media_destination,
    relative_media_destination
):
    """
    Given a folder of markdown files,
    parse all files into a new folder of HTML files
    """

    search = path.join(source_path, '**/*.md')

    # Copy media into destination
    mergetree(media_path, media_destination)
    print("Copied {media_path} to {media_destination}".format(**locals()))

    for filepath in iglob(search):
        # Get relative paths
        local_path = filepath.replace(source_path, '').strip('/')
        output_path = path.join(destination_path, local_path)[:-3] + '.html'
        relative_media_path = path.relpath(media_path, path.dirname(filepath))

        if not relative_media_destination:
            relative_media_destination = path.relpath(
                media_destination,
                path.dirname(output_path)
            )

        # Check folder exists
        makedirs(path.dirname(output_path), exist_ok=True)

        # Parse the markdown
        (title, html_contents) = parse_file(filepath)
        html_document = parse_template(
            template,
            html_contents,
            title,
            navigation
        )
        html_document = html_document.replace(
            relative_media_path,
            relative_media_destination
        )

        with open(output_path, 'w') as output_file:
            output_file.write(html_document)

        print("Created {output_path}".format(**locals()))


def parse_docs_repo(
    source_repository,
    source_branch,
    build_path,
    template_path,
    nav_path,
    files_folder,
    media_folder,
    media_destination,
    relative_media_destination
):
    """
    Parse a remote git repository of markdown files into HTML files in the
    specified build folder
    """

    with TemporaryDirectory() as repo_folder:
        print("Cloning {source_repository}".format(**locals()))
        if source_branch:
            Repo.clone_from(
                source_repository, repo_folder, branch=source_branch
            )
        else:
            Repo.clone_from(source_repository, repo_folder)

        source_path = path.join(repo_folder, files_folder.strip('/'))
        media_path = path.join(repo_folder, media_folder.strip('/'))
        template_path = template_path or path.join(source_path, 'base.tpl')
        nav_path = nav_path or path.join(source_path, 'navigation.tpl')

        with open(template_path) as base_template:
            template = base_template.read()

        with open(nav_path) as nav_template:
            navigation = nav_template.read()

        parse_files(
            source_path,
            build_path,
            template,
            navigation,
            media_path,
            media_destination,
            relative_media_destination
        )
