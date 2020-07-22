
# external packages
import requests
from builtins import object
from joblib import delayed, Parallel

# Python packages
import json
import os

import re
import logging

# This project
from vds_api_client.types import Rois, Products


# logging
def setup_logging(filelevel=10, streamlevel=20, path=''):
    logger = logging.getLogger('vds_api')
    if len(logger.handlers) == 0:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(os.path.join(path, 'vds_api.log'))
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)8s - %(funcName)s @ thr %(thread)05d' +
                                      '  - %(message)s', datefmt='%Y/%m/%d %I:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        fh.setLevel(filelevel)
        ch.setLevel(streamlevel)

        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

# Usefull functions


def getpar_fromtext(textfile, parameter):
    """
    getpar_fromtext(textfile, parameter):

    Get parameters from a text file which holds parameter and value pairs on each line:
        par1 = val\n
        par2 = val\n
        par3 = val1, val2, val3

    Outputs val as string

    Parameters
    ----------
    textfile: str
        path to textfile
    parameter: str
        name of the parameter to seach for

    Returns
    -------
    str or bool:
        value of parameter

    """
    if textfile is not None and os.path.exists(textfile):
        parameter = parameter.lower()
        found = False
        line = ''
        with open(textfile, "r") as f:
            for line in f:
                if line.lstrip().startswith('#'):
                    continue
                if line.split('=')[0].lstrip().rstrip().lower() == parameter:
                    found = True
                    break
        if not found:
            return None
        par = line.split('=')[1].lstrip().rstrip()
        if len(par.split(',')) > 1:
            par = [p.lstrip().rstrip() for p in par.split(',')]
        elif par.lower() in ['true', 'false', 'yes', 'no']:
            return par.lower() in ['true', 'yes']
    else:
        raise RuntimeError('textfile {} does not exist'.format(textfile))
    return par


def api_get(uri, expected_fn='', out_path='', overwrite=False, str_lvl=20, credentials=None, headers=None):
    logger = setup_logging(streamlevel=str_lvl, path=out_path)
    if not overwrite and os.path.exists(expected_fn):
        logger.debug('File {} exists, skipping download'.format(expected_fn))
        return -1, expected_fn
    logger.debug('Starting request for file {}'.format(os.path.basename(expected_fn)))
    r = requests.get(uri, verify=True, stream=True,
                     auth=(credentials['user'], credentials['passwd']),
                     headers=headers)
    if r.status_code == 200:
        ofname = os.path.join(out_path, r.headers['Content-Disposition'].split('=')[1])
        if os.path.basename(ofname) == 'transparent.png':
            logger.debug('No data available for file {}, skipping download'.format(expected_fn))
            return -2, expected_fn
        logger.info('Writing file: {}'.format(ofname))
        with open(ofname, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return ofname.encode('ascii')
    else:
        logger.warning('Request status = {} - Error in retrieving data from url: {}'.format(r.status_code, uri))
    return r, uri


def mkdirs(path, filepath=None):
    """
    mkdirs(path)

    Make directory tree for path. If path is a file with an extention, only the folders are created.

    Parameters
    ----------
    path: str
        Full path as directory tree or file
    filepath: bool
        Force to think of path as a file (happens also if a '.' is included in the path)
    """
    if filepath:
        basepath = os.path.dirname(path)
    elif '.' in os.path.basename(path):
        basepath = os.path.dirname(path)
    else:
        basepath = path
    try:
        os.makedirs(basepath)
    except OSError:
        if not os.path.isdir(basepath):
            raise OSError('Path ''{}'' does not exist and was not created'.format(path))


def configure(config, defaults, config_file, logger):
    for key, value in config.items():
        if value is None:
            if config_file is not None:
                try:
                    config[key] = getpar_fromtext(config_file, key)
                except RuntimeError:
                    logger.warn('Configuration file was not found')
                    pass
            if config[key] is None:
                if key in defaults:
                    logger.debug('Setting default for {}: {}'.format(key, defaults[key]))
                    config[key] = defaults[key]
                else:
                    logger.warning("Value for key='{}' not set ".format(key))
    return config


class VdsApiBase(object):
    """
    VanderSat API object for easy downloading of VanderSat products

    Parameters
    ----------
    username: str
        Username for the vds api data service
        If left empty, the username will be read from
        the environment variable $VDS_USER
    password: str
        Password for the vds api data service
        If left empty, the username will be read from
        the environment variable $VDS_PASS
    debug: bool or int
        Set True for higher verbosity,
        or use integer to set streamlevel (10 <= all messages, 50 > no messages)
    """
    def __init__(self, username=None, password=None, debug=True):
        self.rois = Rois(None)
        self.products = Products(None)
        streamlevel = debug if isinstance(debug, int) else (10 if debug else 20)
        self.logger = setup_logging(streamlevel=streamlevel)
        self._host = 'maps.vandersat.com/api/v2/'
        self._tested = False
        self._config = None
        self._api_calls = []
        self._out_path = ''
        self._overwrite = None
        self._streaming = True
        self._headers = None
        self._outputs = []
        self._retry = []
        self._skipped = []
        self._ndskipped = []
        self._notreached = 0
        self._failed = []
        if username and password:
            self._credentials = dict(user=username, passwd=password)
        else:
            self.logger.info('Extracting credentials from environment variables')
            self._credentials = dict(user=os.environ.get('VDS_USER', None),
                                     passwd=os.environ.get('VDS_PASS', None))
        self._load_user_info()
        self.logger.info(' ================== VDS_API initialized ==================\n')

    def _load_user_info(self):
        self.products = self.get_products()
        self.rois = self.get_rois()
        self.usr_dict = self.get_user_info()

    def __str__(self):
        show = '{} @ {}'.format(self._credentials['user'], self.host)
        if self._headers is not None and 'X-VDS-UserId' in self._headers:
            show = ('{} --impersonated by-- '.format(self._headers['X-VDS-UserId']) +
                    show + '\n\ttrigger .forget() to remove impersonation')
        return show

    def __repr__(self):
        return str(self)

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        """
        Set the host address

        Parameters
        ----------
        host: str
            One of {'maps', 'staging', 'test'}
        """
        env, ver = re.search(r'^(\w+)\.vandersat.com/api/(v\d)/', self._host).groups()
        if host in ['maps', 'test', 'staging']:
            self._host = '{}.vandersat.com/api/{}/'.format(host, ver)
        else:
            self.logger.critical("Server address unknown, choose from {'maps', 'staging', 'test'}")
            raise ValueError('Unexpected server name received: {}'.format(host))
        self._load_user_info()
        self.logger.debug('Using server address: {}'.format(self._host))

    @property
    def outfold(self):
        if not self._out_path:
            self.logger.debug('Outfold not set')
            return ''
        return self._out_path

    @outfold.setter
    def outfold(self, out_path=''):
        if not os.path.exists(out_path):
            self.logger.info('Created new folder @ {}'.format(out_path))
            mkdirs(out_path)
        self.logger.debug('Outfold set to {}'.format(out_path))
        self._out_path = out_path
        self.logger = setup_logging(self.logger.handlers[0].level,
                                    self.logger.handlers[1].level,
                                    path=out_path)

    def set_outfold(self, path):
        """
        Set the output path to download files to

        Parameters
        ----------
        path: location to download files to
        """
        self.outfold = path

    @property
    def debug(self):
        return self.streamlevel < 20

    @debug.setter
    def debug(self, _state):
        self.logger.error('Cannot change debug state through this property anymore')

    @property
    def streamlevel(self):
        return next(filter(lambda x: type(x) is logging.StreamHandler, self.logger.handlers)).level

    @streamlevel.setter
    def streamlevel(self, level):
        stream_handler = next(filter(lambda x: type(x) is logging.StreamHandler, self.logger.handlers))
        stream_handler.setLevel(level)

    @property
    def overwrite(self):
        return self._overwrite

    @property
    def config(self):
        if self._config is None:
            self.logger.warning('API not yet configured')
        return self._config

    def log_config(self, log_level='DEBUG'):
        """
        Output current configuration to the logger as debug messages

        Parameters
        ----------
        log_level: str
            'DEBUG' or 'INFO'
        """
        for key, value in self.config.items():
            if log_level == 'DEBUG':
                self.logger.debug('CONFIG PARAMETER: {} = {}'.format(key, value))
            elif log_level == 'INFO':
                self.logger.info('CONFIG PARAMETER: {} = {}'.format(key, value))

    def impersonate(self, user_email):
        """
        Impersonate user based on email

        Parameters
        ----------
        user_email: str
        """
        if self._headers is None:
            self._headers = {}
        self._headers['X-VDS-UserId'] = user_email
        self._load_user_info()

    def forget(self):
        """
        Reset impersonation back to normal
        """
        self._headers.pop('X-VDS-UserId')
        if not self._headers:
            self._headers = None
        self._load_user_info()

    def _get_content(self, uri, **kwargs):
        r = requests.get(uri, verify=True, stream=True,
                         auth=(self._credentials['user'], self._credentials['passwd']),
                         headers=self._headers,
                         **kwargs)
        r.raise_for_status()
        return json.loads(r.content)

    def _delete_content(self, uri, **kwargs):
        r = requests.delete(uri, verify=True,
                            auth=(self._credentials['user'], self._credentials['passwd']),
                            headers=self._headers,
                            **kwargs)
        r.raise_for_status()

    def get_user_info(self):
        usr_dict = self._get_content('https://maps.vandersat.com/api/v2/users/me')
        return usr_dict

    def get_products(self):
        """
        Get Product objects from this user account

        Returns
        -------
        products: Products
            Collection of Product objects
        """
        product_json = self._get_content('https://maps.vandersat.com/api/v2/products/')
        products = Products(product_json['products'])
        return products

    def check_valid_products(self, products):
        """
        Check if product api_names exist in this account

        Parameters
        ----------
        products: list or str
        """
        if products is None:
            products = []
        elif isinstance(products, str):
            products = [products]

        out_products = []
        not_available = []
        for prod in products:
            try:
                out_products.append(self.products[prod].api_name)
            except ValueError:
                not_available.append(prod)

        if not_available:
            for prod in not_available:
                self.logger.error('product `{}` not in available products'.format(prod))
            self.logger.info('Choose from {}'.format([p.api_name for p in self.products]))
            raise RuntimeError('Products `{}` not in your product-list'.format(not_available))

        return out_products

    def get_rois(self):
        roi_list = self._get_content('https://maps.vandersat.com/api/v2/rois')['rois']
        return Rois(None if not roi_list else roi_list)

    def check_valid_rois(self, rois):
        """
        Check if product api_names exist in this account

        Parameters
        ----------
        rois: list of (str or int)
        """
        if rois is None:
            rois = []
        elif isinstance(rois, str):
            rois = [rois]

        out_rois = []
        not_available = []
        for roi in rois:
            try:
                out_rois.append(self.rois[roi])
            except ValueError:
                not_available.append(roi)

        if not_available:
            for prod in not_available:
                self.logger.error('roi `{}` not in available rois'.format(prod))
            self.logger.info('Choose from :{}'.format(str(self.rois)))
            raise RuntimeError('Rois `{}` not found in account'.format(not_available))

        return out_rois

    def delete_rois_from_account(self, rois):
        """
        Permanently delete rois from your user account

        Parameters
        ----------
        rois: (list of int) or Rois
            collection of roi ids or an Rois object (filtered)
        """
        if type(rois) is Rois:
            if not rois.filter_applied:
                raise RuntimeError('Apply a .filter on your Rois instance, '
                                   'otherwise all your rois will be deleted')
            else:
                rois = rois.ids_to_list()
        for roi in rois:
            uri = "https://maps.vandersat.com/api/v2/rois/{}".format(roi)
            self._delete_content(uri)
        self.rois = self.get_rois()
        self.logger.info('Deletion successful')

    def gen_uri(self, **kwargs):
        self.logger.warning('gen_uri implemented only for VdsApiV2')
        pass

    def _extract_fn(self, uri, out_path=None):
        if uri:
            self.logger.warning('_extract_fn should not be used in the VdsApiBase class')
        fn = '_.txt'
        fp = os.path.join(self._out_path if out_path is None else out_path, fn)
        return fp

    def api_get(self, uri=None, out_path='', **kwargs):
        """
        Get data through api call as configured (1 by 1 only)

        parameters
        -----------
        uri: str
            if not using predefined configuration, a full url can also be specified
        out_path: str
            overrides the output set by VDS_API.outfold but does not create the folder
        kwargs: str or bool
            name-value pairs that override the configuration dict (e.g. product = 'SM_XN_100')
            providing **kwargs will result in a fresh generated api-call
        """
        if uri:
            self._api_calls.append(uri)
        elif len(kwargs) > 0:
            self.gen_uri(**kwargs)
        if not self._api_calls:
            self.gen_uri()
        if not self._out_path:
            op = out_path
        elif out_path == '':
            op = self._out_path
        else:
            op = out_path
            self.logger.warning('Out path defined both in class and api_get, using api_get output folder')
        processed = []
        for uri in self._api_calls:
            processed.append(api_get(uri, self._extract_fn(uri, op), out_path=op, overwrite=self.overwrite,
                             str_lvl=self.logger.handlers[1].level, credentials=self._credentials, headers=self._headers))
        self.review_results(processed, retry=False)
        self._api_calls = []

    def review_results(self, processed, retry=True):
        for p in processed:
            if type(p) is not tuple:
                self._outputs.append(p)
            elif p[0] == -1:
                self._skipped.append(p[1])
            elif p[0] == -2:
                self._ndskipped.append(p[1])
            else:
                if retry:
                    self._retry.append(p[1])
                else:
                    self._failed.append(p[1])

    def retry(self):
        if self._retry:
            i = 0
            self.logger.info('Starting retries 1 by 1 ({} to go)'.format(len(self._retry)))
            for uri in self._retry:
                i += 1
                self.logger.debug('{} / {} - retry for url =\n{}'.format(i, len(self._retry), uri))
                self.api_get(uri)
        if not self._failed:
            self.logger.info('All downloads successfull')

    def bulk_download(self, n_proc):
        n = len(self._api_calls)
        if n < n_proc:
            n_proc = max(n, 1)
            self.logger.debug('Fewer calls than processes used, reducing n_procs to {}'.format(n_proc))
        processed = Parallel(n_jobs=n_proc)(delayed(api_get)(call,
                                                             expected_fn=self._extract_fn(call),
                                                             out_path=self._out_path,
                                                             overwrite=self.overwrite,
                                                             str_lvl=self.logger.handlers[1].level,
                                                             credentials=self._credentials,
                                                             headers=self._headers) for call in self._api_calls)
        self.logger.info('Checking for error messages')
        self.review_results(processed)
        self.retry()
        self._api_calls = []

    def summary(self):
        self.logger.info('==== VanderSat Application Programming Interface Summary ====')
        self.logger.info('Succesfully downloaded:    {:>4} files'.format(len(self._outputs)))
        self.logger.info('Skipped (exists):          {:>4} files'.format(len(self._skipped)))
        self.logger.info('Skipped (no-data):         {:>4} files'.format(len(self._ndskipped)))
        self.logger.info('Retried:                   {:>4} calls'.format(len(self._retry)))
        self.logger.info('Not reached by intterrupt: {:>4} calls'.format(self._notreached))
        self.logger.info('Failed:                    {:>4} calls'.format(len(self._failed)))
        self.logger.info('                       ================')
        self.logger.info('Total                      {:>4} calls'.format(len(self._outputs) +
                                                                         len(self._skipped) +
                                                                         len(self._ndskipped) +
                                                                         len(self._retry) +
                                                                         self._notreached +
                                                                         len(self._failed)
                                                                         ))

# EOF
