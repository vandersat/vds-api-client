
# Python builtin packages
import sys
import os
import time
from math import floor
from collections import OrderedDict
import re
from glob import glob
from datetime import datetime, timedelta
from io import BytesIO

# Module
from vds_api_client.vds_api_base import VdsApiBase, configure

# External packages
import requests
from retrying import retry
from joblib import Parallel, delayed
import pandas as pd


def progress_bar(n, nchar=25):
    """
    Show a progress bar in stderr with nchar characters for the actual bar

    Parameters
    ----------
    n: float
        Value between 0.0 and 1.0
    nchar: int
        Number of characters to use for the progress bar
    """
    nhash = int(floor(n / (1.0/nchar)))
    pbar = '#'*nhash + ' '*(nchar - nhash)
    _ = sys.stderr.write('[{}] {:0.1f} %\b\r'.format(pbar, n*100))
    # sys.stderr.flush()


def _no_type_error(exception):
    return not isinstance(exception, TypeError) and not isinstance(exception, KeyboardInterrupt)


def _http_error(exception):
    return not isinstance(exception, requests.exceptions.HTTPError)


class VdsApiV2(VdsApiBase):
    """
        Extension of the VdsApiBase class with all api/v2 related methods
    """
    def __init__(self, username=None, password=None, debug=True):
        super(VdsApiV2, self).__init__(username, password, debug=debug)
        self.async_requests = []
        self.uuids = []
        self._remove_after_dowload = []
        self._wait_time = 5
        if glob('*.uuid'):
            self._get_uuid_save()
            self.logger.info('Not downloaded uuids found. Trigger <.queue_uuids_files()> '
                             'to prepare for download')

    def __str__(self):
        basestr = super(VdsApiV2, self).__str__()
        if self.async_requests:
            reqsts = '\n'.join('{i}\t{request}'.format(i=i, request=r)
                               for i, r in enumerate(self.async_requests))
        else:
            reqsts = '\t<EMPTY>, use <.gen_gridded_data_request()> or <.gen_time_series_request()>'
        if self.uuids:
            uuids = '\n'.join('{i}\t{uuid}'.format(i=i, uuid=u)
                              for i, u in enumerate(self.uuids))
        else:
            uuids = '\t<EMPTY>, submit a request to add uuid(s)'
        if self._remove_after_dowload:
            uuids_queued = '\n'.join('{i}\t{uuid}'.format(i=i, uuid=u)
                                     for i, u in enumerate(self._remove_after_dowload))
        else:
            uuids_queued = '\t<EMPTY>, generate uuids and trigger .queue_uuids_files()'

        v2str_1 = ('REQUESTS to be submitted <.submit_async_requests()>: [\n'
                   '{}'
                   '\n ]  ==> .async_requests\n'
                   '\n').format(reqsts)
        v2str_2 = ('UUIDS to queue for download <.queue_uuids_files()> : [\n'
                   '{}'
                   '\n ]  ==> .uuids\n'
                   '\n').format(uuids)
        v2str_3 = ('ready for DOWNLOAD <.download_async_files()> : [\n'
                   '{}\n ]\n'
                   ''.format(uuids_queued))
        v2str = ('\n\n'
                 + v2str_1
                 + v2str_2
                 + v2str_3)
        return basestr + v2str

    def get_prev_requests(self):
        """
        Returns all previous requests
        """
        rqsts = self._get_content('https://maps.vandersat.com/api/v2/api-requests/')['requests']
        return None if not rqsts else rqsts

    def gen_gridded_data_request(self, gen_uri=True, config_file=None, products=None,
                                 start_date=None, end_date=None,
                                 lat_min=None, lat_max=None, lon_min=None, lon_max=None,
                                 file_format=None, zipped=None, nrequests=None,
                                 log_config=False):
        """
        Generate one or more uris for the `gridded-data` enpoint.

        Requests can be split up (and therefore collected faster)
        over a date range using `nrequests`

        Parameters
        ----------
        gen_uri: bool
            Generate the URI to be requested, and add it to the request queue.
            If set to False, this can be used to inspect the settings before
            the .gen_uri() method is called
        config_file: str
            path to the configuration file
        products: list of str
            list of product(s) to get. Each product will be a separate request
        start_date: str or datetime
            date string YYYY-MM-DD
        end_date: str or datetime
            date string YYYY-MM-DD
        lat_min: str or float
        lat_max: str or float
        lon_min: str or float
        lon_max: str or float
        file_format: str
            format to download: [netcdf4, (default: gtiff)]
        zipped: bool
            return files zipped (default: False)
        nrequests: int
            Number of requests to breakup one product's date range
            (faster if set, but limited to 4)
        log_config: bool
            Write the used configuration to the logging file and steam
            with INFO level
        """
        if type(start_date) is datetime:
            start_date = start_date.strftime('%Y-%m-%d')
        if type(end_date) is datetime:
            end_date = end_date.strftime('%Y-%m-%d')
        if lat_min:
            lat_min = str(lat_min)
        if lat_max:
            lat_max = str(lat_max)
        if lon_min:
            lon_min = str(lon_min)
        if lon_max:
            lon_max = str(lon_max)

        config = dict(api_call='gridded-data', products=products, start_date=start_date, end_date=end_date,
                      lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
                      file_format=file_format, zipped=zipped, nrequests=nrequests)
        defaults = dict(file_format='gtiff', zipped=False, nrequests=1)
        config = configure(config, defaults, config_file, self.logger)
        config['products'] = self.check_valid_products(config['products'])
        if not config['file_format'] in ['gtiff', 'netcdf4']:
            raise ValueError('Choose one of ["gtiff", "netcdf4"] for argument file_format')
        self._config = config
        if log_config:
            self.log_config('INFO')
        if gen_uri:
            self.gen_uri()

    def gen_time_series_requests(self, gen_uri=True, config_file=None, products=None,
                                 start_time=None, end_time=None,
                                 lats=None, lons=None, rois=None,
                                 file_format=None,
                                 av_win=None, av_win_dir=None, masked=None, clim=None, t=None,
                                 log_config=False):
        """
        Generate one or more uris for the `[point/roi]-time-series` enpoints.

        Parameters
        ----------
        gen_uri: bool
            Generate the URI to be requested, and add it to the request queue.
            If set to False, this can be used to inspect the settings before
            the .gen_uri() method is called
        config_file: str
            path to the configuration file
        products: list of str
            list of product(s) to get
        start_time: str or datetime
            date string YYYY-MM-DD
        end_time: str or datetime
            date string YYYY-MM-DD
        lats: list of float
            list of latitude values
        lons: list or float
            list of longitude values
        rois: list of (int or str)
            Region id or name
        file_format: str
            Format of the output {[csv], json}
        av_win: int
            For adding a running mean with a avg_window_days day window.
            Direction depends on avg_window_direction setting.
        av_win_dir: str
            centered or backward running average.
            - 'center'
            - 'backward'
        masked: bool
            Include masked data in output
        clim: bool
            Add climatology column calculated based on the average column
        t: int
            Calculate derived root zone as additional column with given smoothing `T` value (days)
        log_config: bool
            Write the used configuration to the logging file and steam
        """
        if type(start_time) is datetime:
            start_time = start_time.strftime('%Y-%m-%d')
        if type(end_time) is datetime:
            end_time = end_time.strftime('%Y-%m-%d')
        if (lons is not None) and (type(lons) not in [list, tuple]):
            lons = [lons]
        if (lats is not None) and (type(lats) not in [list, tuple]):
            lats = [lats]
        if (rois is not None) and (type(rois) not in [list, tuple]):
            rois = [rois]

        config = dict(api_call='time-series', products=products,
                      start_time=start_time, end_time=end_time,
                      lats=lats, lons=lons, rois=rois, file_format=file_format,
                      av_win=av_win, av_win_dir=av_win_dir,
                      masked=masked, clim=clim, t=t)
        defaults = dict(file_format='csv', av_win=0, masked=False,
                        clim=False, t=None, av_win_dir='center',
                        lats=[], lons=[], rois=[])
        config = configure(config, defaults, config_file, self.logger)
        for key in ['lons', 'lats', 'rois', 'products']:
            if type(config[key]) is not list:
                config[key] = [config[key]]
        config['products'] = self.check_valid_products(config['products'])
        config['rois'] = self.check_valid_rois(config['rois'])
        if ((not len(config['lons']) == len(config['lats']))
                or (not config['lons'] and not config['rois'])):
            self.logger.warning('Set either lons/lats or rois, no configuration was done')
            return
        if config['av_win'] < 0:
            raise ValueError('No window_size < 0 allowed, please revise settings')
        if config['av_win_dir'] not in {'center', 'backward'}:
            raise ValueError('Window direction should be in {"center", "backward"}')
        self._config = config
        if log_config:
            self.log_config('INFO')
        if gen_uri:
            self.gen_uri()

    def gen_uri(self, add=True, **kwargs):
        """
        Function to generate the VanderSat API call based on the configuration

        Parameters
        ----------
        add: bool
            Add new requests to possibly existing set of requests. If set to False, all previous
            requests will be dropped
        kwargs: any
            Update config using additional key-value pairs. Updating is done inplace thus the
            new settings are persistently changed. On the instance, call the attribute .config
            to see the names of the settings that can be changed
        """
        if self._config is None:
            self.logger.error('API was not configured. Choose one of the configure methods to setup the parameters')
            return None

        if not add:
            self.async_requests = []

        self._config.update(kwargs)
        products = self._config['products']

        if self._config['api_call'] == 'gridded-data':
            start_dt = datetime.strptime(self._config['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(self._config['end_date'], '%Y-%m-%d')
            # Split requests in time
            if (end_dt - start_dt).days >= self._config['nrequests'] * 10:
                diff = (end_dt - start_dt).days // self._config['nrequests']
                splits = [(start_dt + timedelta(i * diff), start_dt + timedelta((i + 1) * diff - 1))
                          for i in range(self._config['nrequests'] - 1)]
                splits.append((start_dt + timedelta((self._config['nrequests']-1) * diff), end_dt))
            else:
                splits = [(start_dt, end_dt)]
                if self._config['nrequests'] > 1:
                    self.logger.info('Only 1 request made, it is not too large anyways right?')
            for prod in products:
                for start, stop in splits:
                    uri = ('https://{host}products/{prod}/gridded-data?'
                           'lat_min={lami}&lat_max={lama}&lon_min={lomi}&lon_max={loma}&'
                           'start_date={start}&end_date={end}&format={fmt}&zipped={zip}'
                           .format(host=self.host, prod=prod,
                                   lami=self._config['lat_min'], lama=self._config['lat_max'],
                                   lomi=self._config['lon_min'], loma=self._config['lon_max'],
                                   start=start.strftime('%Y-%m-%d'), end=stop.strftime('%Y-%m-%d'),
                                   fmt=self._config['file_format'],
                                   zip='true' if self._config['zipped'] else 'false'))
                    self.async_requests.append(uri)
                    self.logger.debug('Generated URI for {prod} between '
                                      '{start} and {end}: {uri}'.format(prod=prod, start=start, end=stop,
                                                                        uri=uri))

        elif self._config['api_call'] == 'time-series':
            locs = {'point-time-series': ['lat={}&lon={}'.format(lat, lon)
                                          for lat, lon in zip(self._config['lats'], self._config['lons'])],
                    'roi-time-series': ['roi_id={}'.format(self.rois[roi]) for roi in self._config['rois']]}
            for prod in products:
                for endpnt, loc_list in locs.items():
                    for loc in loc_list:
                        uri = ('https://{host}products/{prod}/{endpoint}?'
                               'start_time={start}&end_time={end}&{loc}&format={fmt}'
                               '&avg_window_days={av_win}&avg_window_direction={av_win_dir}'
                               '&include_masked_data={masked}&climatology={clim}'
                               .format(host=self.host, prod=prod, endpoint=endpnt,
                                       start=self._config['start_time'], end=self._config['end_time'],
                                       loc=loc, fmt=self._config['file_format'],
                                       av_win=self._config['av_win'],  # default 0
                                       av_win_dir=self._config['av_win_dir'],
                                       masked='true' if self._config['masked'] else 'false',
                                       clim='true' if self._config['clim'] else 'false'))
                        if self._config['t'] is not None:
                            uri += '&exp_filter_t={:d}'.format(self._config['t'])
                        self.async_requests.append(uri)
                        self.logger.debug('Generated URI: {}'.format(uri))

        else:
            self.logger.error("Only 'gridded-data' and [point/roi]-time-series supported for now")
            raise NotImplementedError

    def _extract_fn(self, uri, out_path=None):
        outprod = re.sub('/download$', '', uri).split('/')[-1]
        fp = os.path.join(self.outfold if out_path is None else out_path, outprod)
        return fp
    
    def _get_uuid_save(self):
        uuids = [uuid.replace('.uuid', '') for uuid in glob('*.uuid')]
        if uuids:
            uuids_new = list(set(uuids).difference(self.uuids))
            if uuids_new:
                self.logger.info('Undownloaded uuids, now added to list')
                self.uuids.extend(uuids_new)

    @retry(wait_exponential_multiplier=5000, wait_exponential_max=15000,
           stop_max_attempt_number=3, retry_on_exception=_http_error)
    def _submit_v2_req(self, call):
        self.logger.debug('Submitting async. request with uri=\n{}'.format(call))
        r1_dict = self._get_content(call)
        uuid = r1_dict['uuid']
        with open('{}.uuid'.format(uuid), 'w') as uuid_save:
            uuid_save.write('{}'.format(call) + '\n')
            uuid_save.flush()
        self.logger.info('Received response uuid: {}'.format(uuid))
        return uuid

    def submit_async_requests(self, n_jobs=1, queue_files=True):
        """
        Submit the requests to the VanderSat backend to start the
        processing jobs and retrieve the uuids attached to each job

        After this command, run the `get_v2_files` method to download
        the files attached to the received uuids after they finished
        processing

        Parameters
        ----------
        n_jobs: int
            Submit this amount of simultaneous jobs.
            Should not be necessary > 1 since queing speed
            improved drastically
        queue_files: bool
            Also queue files once all processing is finished. This can
            take a long time.
        """
        if not self.async_requests:
            self.gen_uri()

        self.async_requests = list(OrderedDict.fromkeys(self.async_requests))

        n_jobs = min(min(max(len(self.async_requests), 1), n_jobs), 8)
        uuids = Parallel(n_jobs=n_jobs, require='sharedmem')(delayed(self._submit_v2_req)(call)
                                                             for call in self.async_requests)
        self.uuids.extend(uuids)
        self.async_requests = []
        if queue_files:
            self.queue_uuids_files()

    @retry(wait_exponential_multiplier=5000, wait_exponential_max=15000,
           stop_max_attempt_number=7, retry_on_exception=_no_type_error)
    def _uuid_status(self, uuid, wait_for_complete=True):
        status_url = 'https://' + self.host + 'api-requests/{}/status'.format(uuid)
        self.logger.debug('Status request for UUID: {}'.format(uuid))
        status_dict = self._get_content(status_url)
        while status_dict['percentage'] < 100 and wait_for_complete:
            time.sleep(self._wait_time)
            status_dict = self._get_content(status_url)
            _ = sys.stderr.write('\t' * 20 + '\b\r')
            progress_bar(status_dict['percentage'] / 100.0)
        self.logger.info('Ready for download UUID: {}'.format(uuid))
        return status_dict

    def queue_uuids_files(self, uuids=None):
        if uuids is None:
            self._get_uuid_save()
            uuids = self.uuids
        if type(uuids) not in [list, set, tuple]:
            uuids = set(uuids)
        while uuids:
            uuid = self.uuids.pop(0)
            content = self._uuid_status(uuid)
            uris = content['data']
            self._api_calls += ['http://' + self.host + re.sub(r'^/api/v\d/', '', uri) + '/download' for uri in uris]
            self._remove_after_dowload.append(uuid)

    def download_async_files(self, uuids=None, n_proc=1):
        self.queue_uuids_files(uuids)
        self._api_calls = list(set(self._api_calls))  # Remove double entries
        self.bulk_download(n_proc)
        uuids = self._remove_after_dowload
        with open(time.strftime('download_%Y-%m-%dT%H%M%S.uuids'), 'w') as f:
            f.write('\n'.join(uuids) + '\n')
            f.flush()
        for uuid in uuids:
            if os.path.exists(uuid + '.uuid'):
                os.remove(uuid + '.uuid')

    def get_value(self, product, date, lon, lat):
        """
        Get product values at these indices and return them as arrays

        Parameters
        ----------
        product: str
            Product api_name
        date: str or datetime
            Date of the requested point
        lon: str or float
            Longitude of requested point
        lat: str or float
            Latitude of requested point
        """
        self.check_valid_products(product)
        date = date if isinstance(date, str) else date.strftime('%Y-%m-%dT%H%M%S')
        uri = ('http://{host}products/{product}/point-value?'
               'lat={lat}&lon={lon}&date={date}').format(host=self.host,
                                                         product=product,
                                                         date=date,
                                                         lat=lat,
                                                         lon=lon)
        return self._get_content(uri)['value']

    def get_roi_df(self, product, roi, start_date, end_date):
        """
        Method to querry streamed json output and transform this into
        a pandas DataFrame

        Parameters
        ----------
        product: str
            Product to extract dataframe from
        roi: int or tr
            Region of interest to retrieve DataFrame from
        start_date: str
            start date to retrieve data yyyy-mm-dd
        end_date: str
            end date to retrieve data yyyy-mm-dd (inclusive)

        Returns
        -------
        dfs_lis: list of pd.DataFrame

        """
        roi = self.rois[roi]
        uri = ('https://maps.vandersat.com/api/v2/products/{product}/roi-time-series-sync?'
               'roi_id={roi}&start_time={start_time}&end_time={end_time}&climatology=true&'
               'avg_window_direction=backward&avg_window_days=20&format=csv'
               .format(product=product, roi=roi, start_time=start_date, end_time=end_date))
        r = requests.get(uri, verify=True, stream=True,
                         auth=(self._credentials['user'], self._credentials['passwd']),
                         headers=self._headers)
        r.raise_for_status()
        csv = BytesIO()
        for chunk in r.iter_content(2048):
            csv.write(chunk)
        csv.seek(0)
        df = pd.read_csv(csv, index_col=0, parse_dates=True, dayfirst=True, comment='#')
        csv.close()
        return df

# EOF
