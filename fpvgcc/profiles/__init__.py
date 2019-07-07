

from .context import ContextBase
from .gcc_msp430 import ProfileGccMsp430


def _load_profiles():
    return {
        'default': ContextBase,
        ProfileGccMsp430.id: ProfileGccMsp430,
    }


profiles = _load_profiles()


def get_profile(idn):
    if idn in profiles.keys():
        return profiles[idn]()
    else:
        return profiles['default']()

