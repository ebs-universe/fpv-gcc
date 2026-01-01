

from .context import ContextBase
from .arm_gnu_toolchain import ProfileArmGnuToolchain
from .gcc_msp430 import ProfileGccMsp430


def _load_profiles():
    return {
        'default': ContextBase,
        ProfileArmGnuToolchain.id: ProfileArmGnuToolchain,
        ProfileGccMsp430.id: ProfileGccMsp430,
    }


profiles = _load_profiles()


def get_profile(idn):
    if idn in profiles.keys():
        return profiles[idn]()
    else:
        return profiles['default']()
