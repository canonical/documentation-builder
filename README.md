Ubuntu documentation builder
===

A tool for building a set of documentation files in HTML format,
from a remote git repository containing markdown files.

Installation
---

``` bash
pip3 install ubuntudesign.documentation-builder
```

Usage
---

The basic usage will build the markdown files from a remote repository in the standard format into the local directory:

``` bash
$ documentation-builder --source-repository git@github.com:juju/docs.git --media-destination media
```

There are many options for more advanced usage:

``` bash
$ documentation-builder \
    --repository git@github.com:juju/docs.git  `# Where to pull the markdown files from`
    --branch new-version                       `# To pull from a different branch than the default`
    --build-path build                         `# Where to place the built files`
    --media-destination build/media            `# Where to place the media files from the repository`
    --template-path wrapper.tpl                `# Path to an alternate wrapping template for the build HTML files`
    --nav-path nav.html                        `# Path to an alternative navigation than the one provided in the repository`
    --files-folder docs                        `# An alternative location inside the repository to look for markdown files (default: src)`
    --media-folder media                       `# An alternative location inside the repository to look for media files (default: media)`
    --relative-media-destination               `# A URL base for linking to media inside the built HTML files (defaults to relative path to built media location - e.g.: ../media)`
    --no-link-extensions                       `# Don't include '.html' extension in internal links`
