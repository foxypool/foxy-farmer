import chia

from foxy_farmer.version import version

chia_version = chia.__version__


def monkey_patch_chia_version():
    if "+" in chia_version:
        chia.__version__ = f"{chia_version}-ff-{version}"
    else:
        chia.__version__ = f"{chia_version}+ff-{version}"
