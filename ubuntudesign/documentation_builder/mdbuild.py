#!/usr/bin/env python3
"""
A tool to convert Juju docs markdown -> html
"""

# Core modules
import re
import codecs
from os import path, makedirs, walk

# Third party modules
import markdown

# config

extlist = [
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
extcfg = []

# global
args = []
doc_nav = ''
default_title = 'Juju Documentation'


def getoutfile(filename, outpath):
    base = path.basename(filename)
    base = path.splitext(base)[0] + '.html'
    return path.join(outpath, base)


def build(
    source='./src/',
    outpath='./htmldocs',
    template_path=None,
    nav_path=None,
    filepath=None,
    debug=False,
    quiet=None,
    todo=None
):
    global args

    template_path = template_path or path.join(source, 'base.tpl')

    with open(template_path) as base_template:
        template = base_template.read()

    nav_path = nav_path or path.join(source, 'navigation.tpl')

    with open(nav_path) as nav_template:
        navigation = nav_template.read()

    mdparser = markdown.Markdown(extensions=extlist)

    if (filepath):
        page = Page(
            filepath[0],
            mdparser,
            template,
            navigation
        )
        page.convert()
        page.write(getoutfile(page.filename, outpath))
        print(page.output)

    elif (todo):
        lang = 'en'
        out = codecs.open("TODO.txt", "w", encoding='utf-8')
        src_path = path.join(source, lang)

        for mdfile in next(walk(src_path))[2]:
            if (path.splitext(mdfile)[1] == '.md'):
                page = Page(
                    path.join(src_path, mdfile),
                    mdparser,
                    template,
                    navigation
                )
                page.convert()

                if 'todo' in page.parser.Meta:
                    out.write(mdfile+":\n")

                    for i in page.parser.Meta['todo']:
                        out.write(' - '+i+'\n')

    else:
        for lang in next(walk(source))[1]:
            output_path = path.join(outpath, lang)

            if not path.exists(output_path):
                makedirs(output_path)

            src_path = path.join(source, lang)

            for mdfile in next(walk(src_path))[2]:
                if (path.splitext(mdfile)[1] == '.md'):
                    if not quiet:
                        print("processing: ", mdfile)

                    p = Page(
                        path.join(src_path, mdfile),
                        mdparser,
                        template,
                        navigation
                    )
                    p.convert()
                    p.write(getoutfile(p.filename, output_path))
                else:
                    if not quiet:
                        print("skipping ", mdfile)


class Page:

    """A page of data"""

    def __init__(self, filename, mdparser, template, navigation):
        self.filename = filename
        self.parser = mdparser
        self.template = template
        self.navigation = navigation
        self.content = ''
        self.parsed = ''
        self.output = ''
        self.load_content()

    def load_content(self):
        i = codecs.open(self.filename, mode="r", encoding="utf-8")
        self.content = i.read()

    def convert(self):
        self.pre_process()
        self.parse()
        self.post_process()

    def pre_process(self):
        """Any actions which should be taken on raw markdown before
           parsing."""
        self.content = self.content
        # self.content = re.sub('\]\(./media/|\]\(media/',
        #                       r'\](../media/',self.content)

    def parse(self):
        self.parsed = self.parser.convert(self.content)

    def post_process(self):
        """Any actions which should be taken on generated HTML
           after parsing."""

        # extract metadata
        if 'title' in self.parser.Meta:
            title = self.parser.Meta['title'][0]
        else:
            title = default_title

        self.output = self.template

        # replace tokens
        replace = [
            ('%%TITLE%%', title),
            ('%%CONTENT%%', self.parsed),
            ('%%DOCNAV%%', self.navigation),
            ('src="media/', 'src="../media/'),
            ('src="./media/', 'src="../media/'),
            ('code class="', 'code class="language-')
        ]
        for pair in replace:
            self.output = re.sub(pair[0], pair[1], self.output)

        self.parser.reset()

    def write(self, outfile):

        if not path.exists(path.dirname(outfile)):
            makedirs(path.dirname(outfile))
        file = codecs.open(outfile, "w", encoding="utf-8",
                           errors="xmlcharrefreplace")
        file.write(self.output)
        file.close


if __name__ == "__main__":
    main()
