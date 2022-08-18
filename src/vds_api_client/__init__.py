
import pkg_resources
import logging

__version__ = pkg_resources.get_distribution(__name__).version

from vds_api_client.api_v2 import VdsApiV2


AUTH = (None, None)
ENVIRONMENT = 'maps'
HEADERS = {}
LOGGER = logging.getLogger('vds_api')

# EOF
