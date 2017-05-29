
Usage
=====

The primary entry point for use of ``fpvgcc`` is as a console script. The
``fpvgcc`` console entry point supports a variety of analysis functions, each
of which essentially recasts the information contained in the provided mapfile
in a different way.

Script usage and arguments are listed here. This help listing can also be
obtained on the command line with ``fpvgcc --help``.

.. argparse::
    :module: fpvgcc.fpv
    :func: _get_parser
    :prog: fpvgcc
    :nodefault:

The various available analysis functions are described below. Additional
analysis may be possible using changes to the code, and is not covered in
this documentation.

Memory Utilization Summaries
----------------------------

These functions print out a concise summary of memory utilization.

.. rubric:: --sar

Prints out a summary of memory utilization per library archive file, sorted by
the total static memory footprint of each file. Object files which were included
directly show up here as object files.

.. code-block:: console

    $ fpvgcc app.map --sar
    +-----------------------------------+--------+--------+----------+------+------+-------+-------+
    | FILE                              | VECT47 | VECT57 | RESETVEC |  ROM |  RAM | HIROM | TOTAL |
    +-----------------------------------+--------+--------+----------+------+------+-------+-------+
    | TOTALS                            |      2 |      2 |        2 | 6588 | 1222 |     0 |       |
    | libmodbus-msp430f5529.a           |      0 |      0 |        0 | 2594 |  360 |     0 |  2954 |
    (...)                             (...)                        (...)                       (...)
    | crtend.o                          |      0 |      0 |        0 |   36 |    2 |     0 |   38  |
    | crtn.o                            |      0 |      0 |        0 |   12 |    0 |     0 |   12  |
    | libprintf-msp430f5529.a           |      0 |      0 |        0 |    0 |    0 |     0 |   0   |
    | libmul_f5.a                       |      0 |      0 |        0 |    0 |    0 |     0 |   0   |
    +-----------------------------------+--------+--------+----------+------+------+-------+-------+

.. rubric:: --sobj ARFILE

Prints out a summary of memory utilization per object file, sorted by the total
static memory footprint of each file.

The ``ARFILE`` specified should be one of the following :

    - ``all`` : All object files included
    - An archive file : Object files provided by that archive file are only listed

.. code-block:: console

    $ fpvgcc app.map --sobj libc.a
    +-----------------+--------+--------+----------+-----+-----+-------+-------+
    | OBJFILE         | VECT47 | VECT57 | RESETVEC | ROM | RAM | HIROM | TOTAL |
    +-----------------+--------+--------+----------+-----+-----+-------+-------+
    | TOTALS          |      0 |      0 |        0 |  96 |   0 |     0 |       |
    | lib_a-memmove.o |      0 |      0 |        0 |  58 |   0 |     0 |   58  |
    | lib_a-memcpy.o  |      0 |      0 |        0 |  20 |   0 |     0 |   20  |
    | lib_a-memset.o  |      0 |      0 |        0 |  18 |   0 |     0 |   18  |
    +-----------------+--------+--------+----------+-----+-----+-------+-------+

.. rubric:: --ssym FILE

Prints out a summary of memory utilization per symbol, sorted by the total
static memory footprint of each symbol.

The ``FILE`` specified should be one of the following :

    - ``all`` : All symbols included
    - An object file : Symbols provided by that object file are only listed
    - An archive file : Symbols provided by that archive file are only listed

.. code-block:: console

    $ fpvgcc app.map --ssym libc.a
    +-----------------+--------+--------+----------+-----+-----+-------+-------+
    | SYMBOL          | VECT47 | VECT57 | RESETVEC | ROM | RAM | HIROM | TOTAL |
    +-----------------+--------+--------+----------+-----+-----+-------+-------+
    | TOTALS          |      0 |      0 |        0 |  96 |   0 |     0 |       |
    | memmove         |      0 |      0 |        0 |  58 |   0 |     0 |   58  |
    | memcpy          |      0 |      0 |        0 |  20 |   0 |     0 |   20  |
    | memset          |      0 |      0 |        0 |  18 |   0 |     0 |   18  |
    | lib_a-memset_o  |      0 |      0 |        0 |   0 |   0 |     0 |   0   |
    | lib_a-memmove_o |      0 |      0 |        0 |   0 |   0 |     0 |   0   |
    | lib_a-memcpy_o  |      0 |      0 |        0 |   0 |   0 |     0 |   0   |
    +-----------------+--------+--------+----------+-----+-----+-------+-------+

.. rubric:: --ssec

Prints out a summary of memory utilization per object file, per section.


Linker Map Nodes
----------------

These functions print out a (relatively) concise version of all linker map
nodes satisfying certain criteria. The output contains all nodes satisfying the
given criteria, including those in DISCARDED sections.

.. rubric:: --lmap ROOT

Prints out all linker map nodes which are apparant descendents of the given
root node. The ``ROOT`` node **must** be provided.

If ROOT is 'root', i.e., the root node of the entire linker map, the output
contains all the top level nodes (first children of 'root') of the linker map,
and only the top level nodes.

For all other provided nodes, the output contains all descendents.

.. code-block:: console

    $ fpvgcc app.map --lmap root
    .__interrupt_vector_1.......................................                                                 UNDEF
    (...)
    .__interrupt_vector_47......................................0x0000ffdc              2         2         2    VECT47         uart_handlers.c.obj
    (...)
    .__reset_vector.............................................0x0000fffe              2                   2    RESETVEC
    .rodata.....................................................0x00004400            234                 234    ROM
    (...)
    .bss........................................................0x00002414           1202                1202    RAM
    (...)
    .lowtext....................................................0x00004550            102                 102    ROM
    .text.......................................................0x00005cca           6172                6172    ROM            slli.o
    (...)

.. code-block:: console

    $ fpvgcc app.map --lmap .lowtext
    .lowtext....................................................0x00004550            102                 102    ROM
    .lowtext.crt_0000start......................................0x00004550                        4         4    ROM            crt0.o
    .lowtext.crt_0100init_bss...................................0x00004554                       14        14    ROM            crt_bss.o
    .lowtext.crt_0300movedata...................................0x00004562                       20        20    ROM            crt_movedata.o
    .lowtext.crt_0700call_init_then_main........................0x00004576                       10        10    ROM            crt_main.o
    .lowtext.crt_0900main_init..................................0x00004580                       54        54    ROM            crt0.o

.. rubric:: --lobj OBJFILE

Prints out all linker map nodes that originated from the specified object file.

.. code-block:: console

    $ fpvgcc app.map --lobj crt_bss.o
    .lowtext.crt_0100init_bss...................................0x00004554                       14        14    ROM            crt_bss.o
    .MSP430.attributes.crt_bss_o................................0x00000353                       23        23    DISCARDED      crt_bss.o

.. rubric:: --lar ARFILE

Prints out all linker map nodes that originated from the specified library
archive file.

.. code-block:: console

    $ fpvgcc app.map --lar libc.a
    .text.memcpy................................................0x00005d3e                       20        20    ROM            lib_a-memcpy.o
    .text.memset................................................0x00005d52                       18        18    ROM            lib_a-memset.o
    .text.memmove...............................................0x00005d64                       58        58    ROM            lib_a-memmove.o
    .MSP430.attributes.lib_a-memcpy_o...........................0x0000030e                       23        23    DISCARDED      lib_a-memcpy.o
    .MSP430.attributes.lib_a-memset_o...........................0x00000325                       23        23    DISCARDED      lib_a-memset.o
    .MSP430.attributes.lib_a-memmove_o..........................0x00000398                       23        23    DISCARDED      lib_a-memmove.o
    .comment.lib_a-memcpy_o.....................................0x00000041                       66        66    DISCARDED      lib_a-memcpy.o
    .comment.lib_a-memset_o.....................................0x00000041                       66        66    DISCARDED      lib_a-memset.o
    .comment.lib_a-memmove_o....................................0x00000041                       66        66    DISCARDED      lib_a-memmove.o


Reverse Address Lookup
----------------------

Given a memory location / address, this function can be used to quickly
determine what exists there. It is expected that this will be useful when
looking through generated assembly listings.

Example:

.. code-block:: console

    $ fpvgcc app.map --addr 0x242e
    .bss........................................................0x00002414           1202                1202    RAM
    .bss.privateXT1ClockFrequency...............................0x0000242e                        4         4    RAM            ucs.c.obj
    $ fpvgcc app.map --addr 0x475d
    .text.clock_set_default.....................................0x000046ce                      144       144    ROM            core_impl.c.obj


Other Information
-----------------

.. rubric:: --lfa

Prints a list of all loaded files. These are all the files that were provided
to the linker. It is not necessary that all of these files have found their way
into the output.

Example :

.. code-block:: console

    $ fpvgcc app.map --lfa
    ../peripherals/libhal-uc-core-msp430f5529.a
    (...)
    /opt/ti/msp430/gcc/bin/../lib/gcc/msp430-elf/5.3.0/../../../../msp430-elf/lib/crt0.o
    (...)
    /opt/ti/msp430/gcc/bin/../lib/gcc/msp430-elf/5.3.0/crtbegin.o
    (...)
    /opt/ti/msp430/gcc/bin/../lib/gcc/msp430-elf/5.3.0/crtend.o
    (...)
    CMakeFiles/firmware-msp430f5529.elf.dir/main.c.obj
    (...)


.. rubric:: --uf

Prints out a list of input files which have non-zero footprint in the output.
If any of the used object files came from a library archive, then only the
library archive is listed. If the object files were used directly, then the
object file is listed. All elements in the output are necessarily represented
by some file in this list, and all these files probably exist(ed) somewhere
in the build tree at the link-time.

.. code-block:: console

    $ fpvgcc app.map --uf
    crt0.o
    libucdm-msp430f5529.a
    (...)
    main.c.obj

.. rubric:: --uarf

Prints out a list of input library archives (.a/.ar) which have non-zero
footprint in the output. Any elements from object files which were used
directly are not represented in this output.

.. code-block:: console

    $ fpvgcc app.map --uarf
    libc.a
    libcrt.a
    libgcc.a
    libhal-uc-core-msp430f5529.a
    (...)

.. rubric:: --uobjf

Prints out a list of input object files (.out) which have non-zero
footprint in the output. All elements in the output are necessarily
represented by some file in this list, though remember that some of
these object files actually exist inside library archives.

.. code-block:: console

    $ fpvgcc app.map --uobjf
    _ashldi3.o
    _clz.o
    _clzdi2.o
    _lshrdi3.o
    _muldi3.o
    _udivdi3.o
    bytebuf.c.obj
    core_impl.c.obj
    crt0.o
    (...)

.. rubric:: --uregions

Prints out a list of used memory regions.

.. code-block:: console

    $ fpvgcc app.map --uregions
    HIROM
    RAM
    RESETVEC
    ROM
    VECT47
    VECT57

.. rubric:: --usections

Prints out a list of used memory sections.

.. code-block:: console

    $ fpvgcc app.map --usections
    .__interrupt_vector_47
    .__interrupt_vector_57
    .__reset_vector
    .bss
    .data
    .lowtext
    .rodata
    .rodata2
    .text

.. rubric:: --la

Prints out a list of detected / assumed section aliases.

.. code-block:: console

    $ fpvgcc app.map --la
    __TI_build_attributes -> .MSP430.attributes
    .gnu.attributes -> .MSP430.attributes
    __interrupt_vector_rtc -> .__interrupt_vector_42
    __interrupt_vector_port2 -> .__interrupt_vector_43
    (...)
