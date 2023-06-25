import chia
import pkg_resources

chia_version = chia.__version__
version = pkg_resources.require("foxy-farmer")[0].version


def monkey_patch_chia_version():
    if "+" in chia_version:
        chia.__version__ = f"{chia_version}-ff-{version}"
    else:
        chia.__version__ = f"{chia_version}+ff-{version}"
