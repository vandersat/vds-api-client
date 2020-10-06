
import os
import pytest
from datetime import datetime
from vds_api_client.api_v2 import VdsApiV2
from vds_api_client.vds_api_base import getpar_fromtext
import pandas as pd


def test_gridded_config(credentials, example_config_area):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.gen_gridded_data_request(gen_uri=False,
                                 config_file=example_config_area,
                                 products=['TEST-PRODUCT_V001_25000'],
                                 start_date='2020-01-01',
                                 end_date=datetime(2020, 1, 3),
                                 nrequests=2)
    assert vds._config == {
        'api_call': 'gridded-data',
        'lat_min': '66', 'lat_max': '67',
        'lon_min': '-6', 'lon_max': '-5',
        'file_format': 'gtiff',
        'start_date': '2020-01-01',
        'end_date': '2020-01-03',
        'products': ['TEST-PRODUCT_V001_25000'],
        'nrequests': 2,
        'zipped': False
    }
    with pytest.raises(RuntimeError):
        vds.gen_gridded_data_request(products=['Nonexisting'])


def test_empty_config(credentials):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    with pytest.raises(RuntimeError):
        vds.gen_uri()


def test_ts_config(credentials, example_config_ts):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.gen_time_series_requests(gen_uri=False,
                                 config_file=example_config_ts,
                                 products=['TEST-PRODUCT_V001_25000'],
                                 start_time=datetime(2020, 1, 1),
                                 end_time='2020-01-03',
                                 lats=[66.875], lons=[-5.875], rois=[25009], masked=True)
    assert vds._config == {
        'api_call': 'time-series',
        'products': ['TEST-PRODUCT_V001_25000'],
        'lats': [66.875], 'lons': [-5.875],
        'rois': [25009],
        'start_time': '2020-01-01',
        'end_time': '2020-01-03',
        'av_win_dir': 'center',
        'file_format': 'csv',
        'av_win': 0,
        'masked': True,
        'clim': False,
        'provide_coverage': False,
        't': None
    }
    with pytest.raises(RuntimeError):
        vds.gen_time_series_requests(products=['Nonexisting'])


def test_gen_uri_grid(credentials, example_config_area):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.gen_gridded_data_request(gen_uri=True, config_file=example_config_area,
                                 start_date='2018-01-01', end_date=datetime(2019, 1, 1),
                                 nrequests=2, log_config=True)
    assert vds.async_requests == [
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/gridded-data?'
        'lat_min=66&lat_max=67&lon_min=-6&lon_max=-5&'
        'start_date=2018-01-01&end_date=2018-07-01&format=gtiff&zipped=false',
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/gridded-data?'
        'lat_min=66&lat_max=67&lon_min=-6&lon_max=-5&'
        'start_date=2018-07-02&end_date=2019-01-01&format=gtiff&zipped=false'
    ]
    vds.gen_uri(zipped=True, nrequests=1)
    assert len(vds.async_requests) == 3
    vds.gen_uri(add=False, file_format='netcdf4', zipped=False)
    assert len(vds.async_requests) == 1
    assert all(['&format=netcdf4' in req for req in vds.async_requests])

    with pytest.raises(ValueError):
        vds.gen_gridded_data_request(gen_uri=True, config_file=example_config_area,
                                     start_date='2018-01-01', end_date=datetime(2019, 1, 1),
                                     file_format='json')  # faulty file_format


def test_gen_uri_ts(credentials, example_config_ts):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.gen_time_series_requests(gen_uri=True, config_file=example_config_ts,
                                 products=['TEST-PRODUCT_V001_25000'],
                                 log_config=True)
    async_requests_should = [
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/point-time-series?'
        'start_time=2020-01-01&end_time=2020-01-03&lat=66.875&lon=-5.875'
        '&format=csv&avg_window_days=0&avg_window_direction=center&include_masked_data=false&climatology=false',
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/point-time-series?'
        'start_time=2020-01-01&end_time=2020-01-03&lat=66.125&lon=-5.125'
        '&format=csv&avg_window_days=0&avg_window_direction=center&include_masked_data=false&climatology=false',
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/roi-time-series?'
        'start_time=2020-01-01&end_time=2020-01-03&roi_id=25009&format=csv'
        '&avg_window_days=0&avg_window_direction=center&include_masked_data=false&climatology=false'
        '&provide_coverage=false',
        'https://staging.vandersat.com/api/v2/products/TEST-PRODUCT_V001_25000/roi-time-series?'
        'start_time=2020-01-01&end_time=2020-01-03&roi_id=25010&format=csv'
        '&avg_window_days=0&avg_window_direction=center&include_masked_data=false&climatology=false'
        '&provide_coverage=false'
    ]

    assert vds.async_requests == async_requests_should
    vds.gen_uri(start_time='2020-01-02')
    assert len(vds.async_requests) == 8
    vds.gen_uri(add=False, file_format='json')
    assert len(vds.async_requests) == 4
    vds.async_requests = []
    vds.gen_time_series_requests(gen_uri=True, products=['TEST-PRODUCT_V001_25000'],
                                 start_time='2020-01-01', end_time='2020-01-03',
                                 lons=[-5.875, -5.125], lats=[66.875, 66.125],
                                 rois=[25009, 'Right'],
                                 log_config=True)
    assert vds.async_requests == async_requests_should

    with pytest.raises(ValueError):
        vds.gen_time_series_requests(gen_uri=True, products=['TEST-PRODUCT_V001_25000'],
                                     start_time='2020-01-01', end_time='2020-01-03',
                                     rois=[25009], av_win=-10)  # Invalid window size

    with pytest.raises(ValueError):
        vds.gen_time_series_requests(gen_uri=True, products=['TEST-PRODUCT_V001_25000'],
                                     start_time='2020-01-01', end_time='2020-01-03',
                                     rois=[25009], av_win_dir='forward')  # Invalid window direction


def test_getarea(credentials, example_config_area, tmpdir):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.set_outfold(tmpdir)
    vds.gen_gridded_data_request(config_file=example_config_area, products=['TEST-PRODUCT_V001_25000'])
    vds.submit_async_requests(queue_files=False)
    uuid = list(vds.uuids)[0]
    assert os.path.exists(uuid + '.uuid')
    fns_should = [os.path.join(tmpdir, fn).format(uuid[:5]) for fn in
                  ['TEST-PRODUCT_V001_25000_2020-01-03T000000_-6.000000_67.000000_-5.000000_66.000000_{}.tif',
                   'TEST-PRODUCT_V001_25000_2020-01-02T000000_-6.000000_67.000000_-5.000000_66.000000_{}.tif',
                   'TEST-PRODUCT_V001_25000_2020-01-01T000000_-6.000000_67.000000_-5.000000_66.000000_{}.tif']]

    assert not any([os.path.exists(fn) for fn in fns_should])
    vds.download_async_files()
    assert all([os.path.exists(fn) for fn in fns_should])
    assert not os.path.exists(uuid + '.uuid')


def test_getts(credentials, example_config_ts, tmpdir):
    vds = VdsApiV2(credentials['user'], credentials['pw'])
    vds.environment = 'staging'
    vds.outfold = tmpdir
    vds.gen_time_series_requests(gen_uri=True, config_file=example_config_ts, rois=[])
    vds.submit_async_requests(queue_files=False)
    uuids = list(vds.uuids)
    fns_should = [fn.format(uuid[:5]) for fn, uuid in zip(
                  ['ts_TEST-PRODUCT_V001_25000_2020-01-01T000000_2020-01-03T000000_-5.875000_66.875000_{}.csv',
                   'ts_TEST-PRODUCT_V001_25000_2020-01-01T000000_2020-01-03T000000_-5.125000_66.125000_{}.csv'
                   ], vds.uuids)]
    assert all([os.path.exists(uuid + '.uuid') for uuid in uuids])
    vds.download_async_files()
    filenames = os.listdir(tmpdir)
    assert sorted(filenames) == sorted(fns_should)
    assert not all([os.path.exists(uuid + '.uuid') for uuid in uuids])


def test_get_df(example_config_ts):
    vds = VdsApiV2()
    vds.environment = 'staging'
    rois = getpar_fromtext(example_config_ts, 'rois')
    product = getpar_fromtext(example_config_ts, 'products')
    df = vds.get_roi_df(product, rois[0], '2020-01-01', '2020-01-03')
    assert isinstance(df, pd.DataFrame)

# EOF
