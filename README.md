# fpv-gcc
Analysing (MSP430-)GCC generated Map files for measuring code footprint

Example output with an MSP430-ELF-GCC map file
----------------------------------------------

    +--------------------------------+--------+----------+-------+------+-------+-----------+-------+
    | FILE                           | VECT52 | RESETVEC |   ROM |  RAM | HIROM | DISCARDED | TOTAL |
    +--------------------------------+--------+----------+-------+------+-------+-----------+-------+
    | TOTALS                         |      2 |        2 | 14504 | 1314 |     0 |    141825 |       |
    | libusb-api-msp430f5529.a       |      0 |        0 |  6580 |  200 |     0 |     49609 | 56389 |
    | libdriverlib-msp430f5529.a     |      0 |        0 |  1756 |    8 |     0 |     26550 | 28314 |
    | libprintf-msp430f5529.a        |      0 |        0 |  1314 |    0 |     0 |      7945 |  9259 |
    | UsbIsr.c.obj                   |      2 |        0 |  1252 |    0 |     0 |      6522 |  7776 |
    | main.c.obj                     |      0 |        0 |   358 |   22 |     0 |      7144 |  7524 |
    | libgcc.a                       |      0 |        0 |   546 |    0 |     0 |      5201 |  5747 |
    | libbc-iface-usb-msp430f5529.a  |      0 |        0 |   304 |  212 |     0 |      4436 |  4952 |
    | libusb-app-msp430f5529.a       |      0 |        0 |   136 |    0 |     0 |      4586 |  4722 |
    | libbytebuf-msp430f5529.a       |      0 |        0 |   270 |    0 |     0 |      4414 |  4684 |
    | libmodbus-msp430f5529.a        |      0 |        0 |    70 |  612 |     0 |      3837 |  4519 |
    | libusb-config-msp430f5529.a    |      0 |        0 |  1034 |    2 |     0 |      3163 |  4199 |
    | libc.a                         |      0 |        0 |    82 |    0 |     0 |      4045 |  4127 |
    | libucdm-msp430f5529.a          |      0 |        0 |     0 |  224 |     0 |      3649 |  3873 |
    | libhal-uc-core-msp430f5529.a   |      0 |        0 |   154 |    0 |     0 |      2180 |  2334 |
    | libcontrol-iface-msp430f5529.a |      0 |        0 |   100 |    0 |     0 |      1995 |  2095 |
    | libprbs-msp430f5529.a          |      0 |        0 |    22 |    0 |     0 |      1807 |  1829 |
    | libboard-funcs-msp430f5529.a   |      0 |        0 |     6 |    8 |     0 |      1414 |  1428 |
    | libcrt.a                       |      0 |        0 |    44 |    0 |     0 |      1257 |  1301 |
    | crt0.o                         |      0 |        2 |    72 |    0 |     0 |      1192 |  1266 |
    | crtbegin.o                     |      0 |        0 |   344 |   24 |     0 |       271 |  639  |
    | crtn.o                         |      0 |        0 |    12 |    0 |     0 |       460 |  472  |
    | crtend.o                       |      0 |        0 |    48 |    2 |     0 |       148 |  198  |
    +--------------------------------+--------+----------+-------+------+-------+-----------+-------+

Example output with an AVR-GCC map file
---------------------------------------

    +-----------------+-------+-----------+------+--------+--------+
    | FILE            |  text | DISCARDED | data | eeprom | TOTAL  |
    +-----------------+-------+-----------+------+--------+--------+
    | TOTALS          | 43446 |    467078 | 1266 |      0 |        |
    | crtm644.o       |    28 |    318544 |    0 |      0 | 318572 |
    | Comm.o          |  7554 |     31746 |   77 |      0 | 39377  |
    | libsys.a        |  6041 |     26076 |  168 |      0 | 32285  |
    | Application.o   |  6875 |     15370 |  442 |      0 | 22687  |
    | libavr.a        |  1758 |     11556 |  190 |      0 | 13504  |
    | libm.a          |  1398 |      9720 |    0 |      0 | 11118  |
    | libc.a          |  1700 |      7914 |   10 |      0 |  9624  |
    | libprintf_flt.a |  3580 |      5142 |    0 |      0 |  8722  |
    | Calibration.o   |  4808 |      3366 |    0 |      0 |  8174  |
    | CM.o            |  1877 |      4902 |   84 |      0 |  6863  |
    | CS.o            |  1405 |      5310 |   61 |      0 |  6776  |
    | VM.o            |  1464 |      4782 |   84 |      0 |  6330  |
    | VS.o            |  1092 |      4734 |   61 |      0 |  5887  |
    | VM2.o           |  1320 |      4410 |   18 |      0 |  5748  |
    | RM.o            |  1056 |      4158 |   10 |      0 |  5224  |
    | libutils.a      |   614 |      2442 |    0 |      0 |  3056  |
    | Storage.o       |   252 |      2670 |   12 |      0 |  2934  |
    | SystemConfig.o  |   268 |      2322 |   40 |      0 |  2630  |
    | LEDDisplay.o    |    56 |      1914 |    9 |      0 |  1979  |
    | libgcc.a        |   300 |         0 |    0 |      0 |  300   |
    +-----------------+-------+-----------+------+--------+--------+
