    **Archived**
    
    This project is legacy and should not be used for new documentation. Existing documentation projects using it should be migrated to `the Discourse model <https://canonical-webteam.github.io/practices/project-structure/documentation.html#community-documentation>`_, or use another solution. If you manage such a project, please reach out to us to facilitate the upgrade.
    
----

Ubuntu documentation builder
============================

Maintenance mode
----------------

`documentation-builder` is now considered a legacy product, as all user maintained documentation sets should now be moving to the `discourse-docs model <https://canonical-webteam.github.io/practices/project-structure/documentation.html#community-documentation>`__.

Important fixes will still be performed, but we will not be adding new features.

----

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

The best way to install `documentation-builder` is with `snap <https://snapcraft.io>`__:

.. code:: bash

    sudo snap install documentation-builder

If you don't have `snap`  on your system, you can also install it with `pip3`:

.. code:: bash

    pip3 install ubuntudesign.documentation-builder

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

    documentation-builder --source-folder docs  # build the documentation-builder's own documentation
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

Debugging
*********

To run a specific test:

.. code:: bash

    ./setup.py test --addopts tests/test_operations.py::test_find_files

You can debug tests by `adding a debugger to the code <https://www.safaribooksonline.com/blog/2014/11/18/intro-python-debugger/>`__ and running the test again.
