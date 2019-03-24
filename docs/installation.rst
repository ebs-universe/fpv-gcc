
Installation
============

Installation from PyPI
----------------------

``fpvgcc`` can be installed normally from the Python Package Index. The
``fpvgcc`` script entry point will also be installed to your ``$PATH`` and
will be available for use from your terminal.

Note that you will need write access to your python packages folder. This
means you will have to install as root or with sudo on most linux distributions,
unless you are installing to a virtual environment you can write to.

.. code-block:: console

    $ sudo pip install fpvgcc
    $ fpvgcc
    usage: fpvgcc [-h] [-v]
              (--sar | ... )
    fpvgcc: error: too few arguments


Installation from Sources
-------------------------

The sources can be downloaded from the project's
`github releases <https://github.com/chintal/fpv-gcc/releases>`_. While this
is the least convenient method of installation, it does have the advantage of
making the least assumptions about your environment.

You will have to ensure the following dependencies are installed and available
in your python environment by whatever means you usually use.

    - six
    - prettytable


.. code-block:: console

    $ wget https://github.com/chintal/fpv-gcc/archive/v0.8.2.zip
    $ unzip fpv-gcc-0.8.2.zip
    ...
    $ cd fpv-gcc-0.8.2
    $ sudo python setup.py install
    ...
    $ fpvgcc
    usage: fpvgcc [-h] [-v]
              (--sar | ... )
    fpvgcc: error: too few arguments


Installation for Development
----------------------------

Installation from the repository is the most convenient installation method
if you intend to modify the code, either for your own use or to contribute to
``fpvgcc``.

.. code-block:: console

    $ git clone https://github.com/chintal/fpv-gcc.git
    $ cd fpv-gcc
    $ sudo pip install -e .
    $ fpvgcc
    usage: fpvgcc [-h] [-v]
              (--sar | ... )
    fpvgcc: error: too few arguments
