
from vds_api_client.api_cli import api
import os


def test_base_cli(runner):
    result = runner.invoke(api)
    assert result.exit_code == 0


def test_cli_test(runner):
    result = runner.invoke(api, ['--environment', 'staging', 'test'])
    assert result.exit_code == 0


def test_cli_info(runner):
    result = runner.invoke(api, ['--environment', 'staging', 'info'])
    assert result.exit_code == 0


def test_cli_grid_base(runner, tmpdir):
    result = runner.invoke(api, ['--environment', 'staging',
                                 'grid',
                                 '--product', 'TEST-PRODUCT_V001_25000',
                                 '--lon_range', '-5.5', '5.0',
                                 '--lat_range', '66.5', '67',
                                 '--date_range', '2020-01-01', '2020-01-02',
                                 '--n_proc', '1',
                                 '-o', tmpdir])
    assert result.exit_code == 0
    assert not result.exception
    filenames = os.listdir(tmpdir)
    assert len(filenames) == 2


def test_cli_grid_nczip(runner, tmpdir):
    result = runner.invoke(api, ['--environment', 'staging',
                                 'grid',
                                 '--product', 'TEST-PRODUCT_V001_25000',
                                 '--lon_range', '-5.5', '5.0',
                                 '--lat_range', '66.5', '67',
                                 '--date_range', '2020-01-01', '2020-01-02',
                                 '--n_proc', '1',
                                 '--format', 'netcdf4',
                                 '--zipped',
                                 '-o', tmpdir])
    assert result.exit_code == 0
    assert not result.exception
    filenames = os.listdir(tmpdir)
    assert len(filenames) == 1


def test_cli_ts_base(runner, tmpdir):
    result = runner.invoke(api, ['--environment', 'staging',
                                 'ts',
                                 '--product', 'TEST-PRODUCT_V001_25000',
                                 '--latlon', '66.875', '-5.875',
                                 '--latlon', '66.125', '-5.125',
                                 '--roi', '25009', '--roi', 'Right',
                                 '--date_range', '2020-01-01', '2020-01-03',
                                 '-o', tmpdir])
    assert result.exit_code == 0
    assert not result.exception
    filenames = os.listdir(tmpdir)
    assert len(filenames) == 4


def test_cli_v2_ts_allopts(runner, tmpdir):
    result = runner.invoke(api, ['--environment', 'staging', 'ts',
                                 '--product', 'TEST-PRODUCT_V001_25000',
                                 '--latlon', '66.875', '-5.875',
                                 '--date_range', '2020-01-01', '2020-01-03',
                                 '--masked',
                                 '--av_win', '3',
                                 '--clim',
                                 '-t', '10',
                                 '--provide-coverage',
                                 '-o', tmpdir])
    assert result.exit_code == 0
    assert not result.exception
    filenames = os.listdir(tmpdir)
    assert len(filenames) == 1

# EOF
