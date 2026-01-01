from .context import ContextBase

class ProfileArmGnuToolchain(ContextBase):
    id = 'arm-gnu-toolchain'

    def __init__(self):
        super(ProfileArmGnuToolchain, self).__init__()
        self._suppressed_names.extend([
                'attributes',
                'comment',
                'debug',
                'debug_abbrev',
                'debug_aranges',
                'debug_frame',
                'debug_funcnames',
                'debug_info',
                'debug_line',
                'debug_line_str',
                'debug_loc',
                'debug_loclists',
                'debug_macinfo',
                'debug_macro',
                'debug_pubnames',
                'debug_pubtypes',
                'debug_ranges',
                'debug_rnglists',
                'debug_sfnames',
                'debug_srcinfo',
                'debug_str',
                'debug_typenames',
                'debug_varnames',
                'debug_weaknames',
                'line',
        ])
