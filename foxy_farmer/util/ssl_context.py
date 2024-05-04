from chia.server.server import ssl_context_for_root
from chia.ssl.create_ssl import get_mozilla_ca_crt

ssl_context = ssl_context_for_root(get_mozilla_ca_crt())
