

from fpvgcc.fpv import GCCMemoryMapParserSM
from fpvgcc.gccMemoryMap import GCCMemoryMap
from .vectors import example_map


def test_process_map(example_map):
    mm, vectors = example_map
    assert isinstance(mm, GCCMemoryMapParserSM)
    assert isinstance(mm.memory_map, GCCMemoryMap)
