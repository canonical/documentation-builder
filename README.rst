Ubuntu documentation builder
============================

.. image:: https://travis-ci.org/CanonicalLtd/documentation-builder.svg?branch=master
   :alt: build status
   :target: https://travis-ci.org/CanonicalLtd/documentation-builder

.. image:: https://coveralls.io/repos/github/CanonicalLtd/documentation-builder/badge.svg?branch=master
   :alt: code coverage
   :target: https://coveralls.io/github/CanonicalLtd/documentation-builder


A tool for building a set of documentation files in HTML format, from a
remote git repository containing markdown files.

Installation
------------

.. code:: bash

    snap install documentation-builder

For more information see `the documentation <docs/en/>`__.

Development
-----------

documentation-builder is a Python module. The main application code lives in
`ubuntudesign/documentation_builder <ubuntudesign/documentation_builder>`__. Updates
to the markup or styling should be made in `the default template <ubuntudesign/documentation_builder/resources/template.html>`__.

Checking changes
~~~~~~~~~~~~~~~~

To check your changes to documentation-builder, it's probably easiest to install the module locally, in editable mode, within an encapsulated environment:

.. code:: bash

    python3 -m venv env3 && source env3/bin/activate  # Create encapsulated environment
    pip install -e .  # Install the module in editable mode

    bin/documentation-builder --source-folder docs  # build the documentation-builder's own documentation
    xdg-open build/en/index.html  # Open up the documentation page

Watching for changes
~~~~~~~~~~~~~~~~~~~~

On Ubuntu et al. you can use `inotifywait` to watch for changes to the source files, and rebuild when something changes as follows:

.. code:: bash

    sudo apt install inotify-tools  # Ensure inotifywait is installed

    # Force rebuild docs when anything changes in the source folder
    while inotifywait -r -e close_write "./ubuntudesign"; do bin/documentation-builder --force --source-folder docs; done

Tests
~~~~~

To run tests:

.. code:: bash

    ./setup.py test
