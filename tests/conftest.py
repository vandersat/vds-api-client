
import os
import pathlib
from glob import glob
import pytest
from click.testing import CliRunner
import vds_api_client
import tests


@pytest.fixture
def credentials():
    """
    Get the credentials stored in the environent variables `$VDS_USER` and `$VDS_PASS`
    """
    creds = {'user': os.environ.get('VDS_USER'), 'pw': os.environ.get('VDS_PASS')}
    return creds


@pytest.fixture
def example_config_area():
    """
    Get the configuration for Aa en Maas downloads
    """
    filename = os.path.join('tests', 'config_files', 'example_config_area.vds')
    return filename


@pytest.fixture
def example_config_ts():
    """
    Get the configuration for Aa en Maas downloads
    """
    filename = os.path.join('tests', 'config_files', 'example_config_ts.vds')
    return filename


@pytest.fixture
def runner():
    """
    Get the cli runner
    """
    return CliRunner()


@pytest.fixture(autouse=True)
def clean_uuid_files():
    """
    Get the cli runner
    """
    files_to_delete = glob('*.uuid')
    for filename in files_to_delete:
        os.remove(filename)


@pytest.fixture(autouse=True)
def set_environment_staging():
    vds_api_client.ENVIRONMENT = 'staging'


@pytest.fixture
def testdata_dir():
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    tests_path = pathlib.Path(tests.__file__)
    return os.path.join(tests_path.parent, 'testdata')

# EOF
