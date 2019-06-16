
from .context import ContextBase


class ProfileGccMsp430(ContextBase):
    id = 'elf32-msp430'

    def __init__(self):
        super(ProfileGccMsp430, self).__init__()
        self._suppressed_names.extend([
                'debug_line',
                'debug_info',
                'debug_ranges',
                'debug_aranges',
                'debug_loc',
                'debug_str',
                'debug_frame',
                'debug_abbrev',
                'comment',
                'MSP430'
        ])
