
import os
from glob import glob
import pytest
from click.testing import CliRunner
import vds_api_client


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

# EOF
