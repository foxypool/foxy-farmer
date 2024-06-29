import importlib.metadata

version: str
try:
    version = importlib.metadata.version("foxy-farmer")
except importlib.metadata.PackageNotFoundError:
    # package is not installed
    version = "unknown"
