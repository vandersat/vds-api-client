
import vds_api_client as vac
import json
import requests
import warnings
from builtins import object


class Requester(object):
    """
    Class containing authentication shared accross all modules
    with api methods `get`, `post` and `delete`. Meant as a
    parent class for objects that require requesting capabilities.
    """
    def _load_user_info(self):
        """
        Load the user info, define in subclass
        """
        raise NotImplementedError('Call this on VdsApiV2 or VdsApiBase objects')

    @staticmethod
    def set_auth(auth):
        """Set the authentication tuple
        """
        vac.AUTH = auth

    @property
    def auth(self):
        return vac.AUTH

    @property
    def headers(self):
        """"""
        return vac.HEADERS

    @property
    def host(self):
        """Get the host with the set environment"""
        return f'{vac.ENVIRONMENT}.vandersat.com/api/v2/'

    @host.setter
    def host(self, host):
        """
        Set the host address, will be deprecated

        Parameters
        ----------
        host: str
            One of {'maps', 'staging', 'test'}
        """
        warnings.warn("The `host` property setter will be deprecated soon, use the `environment` "
                      "property to set the environment {'maps', 'staging', 'test'}")
        if host in ['maps', 'test', 'staging']:
            vac.ENVIRONMENT = host
        else:
            self.logger.critical("Environment unknown, choose from {'maps', 'staging', 'test'}")
            raise ValueError('Unexpected server name received: {}'.format(host))
        self._load_user_info()
        self.logger.debug('Using server address: {}'.format(self.host))

    @property
    def environment(self):
        return vac.ENVIRONMENT

    @environment.setter
    def environment(self, environment):
        if environment in ['maps', 'test', 'staging']:
            vac.ENVIRONMENT = environment
        else:
            self.logger.critical("Environment unknown, choose from {'maps', 'staging', 'test'}")
            raise ValueError('Unexpected environment name received: {}'.format(environment))
        self._load_user_info()
        self.logger.debug('Using server address: {}'.format(self.host))

    @property
    def logger(self):
        return vac.LOGGER

    @logger.setter
    def logger(self, logger):
        vac.LOGGER = logger

    def impersonate(self, user_email):
        """
        Impersonate user based on email

        Parameters
        ----------
        user_email: str
        """
        vac.HEADERS['X-VDS-UserId'] = user_email
        self._load_user_info()

    def forget(self):
        """
        Reset impersonation back to normal
        """
        vac.HEADERS.pop('X-VDS-UserId', None)
        self._load_user_info()

    def get(self, uri, **kwargs):
        r = requests.get(uri, verify=True, stream=True,
                         auth=self.auth,
                         headers=vac.HEADERS,
                         **kwargs)
        r.raise_for_status()
        return json.loads(r.content)

    def post(self, uri, **kwargs):
        r = requests.post(uri, verify=True, stream=True,
                          auth=self.auth,
                          headers=vac.HEADERS,
                          **kwargs)
        r.raise_for_status()
        return json.loads(r.content)

    def delete(self, uri, **kwargs):
        r = requests.delete(uri, verify=True,
                            auth=self.auth,
                            headers=vac.HEADERS,
                            **kwargs)
        r.raise_for_status()

# EOF
