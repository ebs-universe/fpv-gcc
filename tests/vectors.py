

import pytest
from fpvgcc.fpv import process_map_file


EXAMPLE_FILES = {
    'tests/maps/example.arm-none-eabi.basic.0.map': None,
    'tests/maps/example.msp430-elf.basic.0.map': None,
    'tests/maps/example.msp430-elf.0.map': None,
}


@pytest.fixture(scope="module",
                params=EXAMPLE_FILES.keys())
def example_map(request):
    filename = request.param
    vectors = EXAMPLE_FILES[filename]
    return process_map_file(filename, profile='auto'), vectors
