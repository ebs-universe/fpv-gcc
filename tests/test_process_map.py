

import pytest
from fpvgcc.fpv import process_map_file

from .vectors import EXAMPLE_FILES


@pytest.mark.parametrize('filename', EXAMPLE_FILES)
def test_process_map(filename):
    mm = process_map_file(filename)
