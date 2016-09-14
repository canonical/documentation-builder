#!/usr/bin/env python3
"""
A tool to convert Juju docs markdown -> html
"""

# Core modules
import os
import re
import codecs
import argparse

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
doc_template = ''
doc_nav = ''
default_title = 'Juju Documentation'


def getoutfile(filename, outpath):
    base = os.path.basename(filename)
    base = os.path.splitext(base)[0] + '.html'
    return os.path.join(outpath, base)


def build(
    source='./src/',
    outpath='./htmldocs',
    filepath=None,
    debug=False,
    quiet=None,
    todo=None
):
    global doc_template
    global doc_nav
    global args
    t = codecs.open(os.path.join(source, 'base.tpl'), encoding='utf-8')
    doc_template = t.read()
    t.close()
    t = codecs.open(
        os.path.join(source, 'navigation.tpl'), encoding='utf-8')
    doc_nav = t.read()
    t.close()
    mdparser = markdown.Markdown(extensions=extlist)
    if (filepath):
        p = Page(filepath[0], mdparser)
        p.convert()
        p.write(getoutfile(p.filename, outpath))
        print(p.output)
    elif (todo):
        lang = 'en'
        out = codecs.open("TODO.txt", "w", encoding='utf-8')
        src_path = os.path.join(source, lang)
        for mdfile in next(os.walk(src_path))[2]:
            if (os.path.splitext(mdfile)[1] == '.md'):
                p = Page(os.path.join(src_path, mdfile), mdparser)
                p.convert()
                if 'todo' in p.parser.Meta:
                    out.write(mdfile+":\n")
                    for i in p.parser.Meta['todo']:
                        out.write(' - '+i+'\n')
    else:
        for lang in next(os.walk(source))[1]:
            output_path = os.path.join(outpath, lang)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            src_path = os.path.join(source, lang)
            for mdfile in next(os.walk(src_path))[2]:
                if (os.path.splitext(mdfile)[1] == '.md'):
                    if not quiet:
                        print("processing: ", mdfile)
                    p = Page(os.path.join(src_path, mdfile), mdparser)
                    p.convert()
                    p.write(getoutfile(p.filename, output_path))
                else:
                    if not quiet:
                        print("skipping ", mdfile)

# Classes


class Page:

    """A page of data"""

    def __init__(self, filename, mdparser):
        self.filename = filename
        self.content = ''
        self.parsed = ''
        self.output = ''
        self.parser = mdparser
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
        # copy template
        self.output = doc_template

        # replace tokens
        replace = [
            ('%%TITLE%%', title),
            ('%%CONTENT%%', self.parsed),
            ('%%DOCNAV%%', doc_nav),
            ('src="media/', 'src="../media/'),
            ('src="./media/', 'src="../media/'),
            ('code class="', 'code class="language-')
        ]
        for pair in replace:
            self.output = re.sub(pair[0], pair[1], self.output)
        self.parser.reset()

    def write(self, outfile):

        if not os.path.exists(os.path.dirname(outfile)):
            os.makedirs(os.path.dirname(outfile))
        file = codecs.open(outfile, "w", encoding="utf-8",
                           errors="xmlcharrefreplace")
        file.write(self.output)
        file.close


if __name__ == "__main__":
    main()
