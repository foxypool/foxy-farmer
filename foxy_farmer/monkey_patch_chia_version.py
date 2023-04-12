import chia
import pkg_resources
version = pkg_resources.require("foxy-farmer")[0].version

chia.__version__ = f"{chia.__version__}-ff-{version}"
