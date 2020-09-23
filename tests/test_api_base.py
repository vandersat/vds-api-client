
import os
from vds_api_client.vds_api_base import VdsApiBase, getpar_fromtext
from vds_api_client.types import Products, Product, Rois, Roi
import pytest


def test_par_from_text(example_config_area):
    lat_min = getpar_fromtext(example_config_area, 'lat_min')
    assert lat_min == '66'
    products = getpar_fromtext(example_config_area, 'products')
    assert products == 'TEST-PRODUCT_V001_25000'
    void = getpar_fromtext(example_config_area, 'nonexisting')
    assert void is None
    with pytest.raises(RuntimeError):
        getpar_fromtext('nonexisting.file', 'lat_min')


def test_login(credentials):
    vds = VdsApiBase(credentials['user'], credentials['pw'])
    assert vds.products is not None


def test_login_from_environment():
    vds = VdsApiBase()
    assert vds.products is not None


def test_load_info(credentials):
    vds = VdsApiBase(credentials['user'], credentials['pw'])
    assert type(vds.usr_dict) is dict
    assert type(vds.rois) is Rois


def test_host_setter(credentials):
    vds = VdsApiBase(credentials['user'], credentials['pw'])
    vds.host = 'staging'
    assert vds.host == 'staging.vandersat.com'
    with pytest.raises(ValueError):
        vds.host = 'nonexisting'


def test_outfold_setter(credentials, tmpdir):
    vds = VdsApiBase(credentials['user'], credentials['pw'])
    assert vds.outfold == ''
    new_dir = os.path.join(tmpdir, 'fold1', 'fold2')
    assert not os.path.exists(new_dir)
    vds.set_outfold(new_dir)
    assert os.path.exists(new_dir)


def test_products(credentials, example_config_area):
    vds = VdsApiBase(credentials['user'], credentials['pw'])
    assert isinstance(vds.products, Products)
    assert all([isinstance(p, Product) for p in vds.products])
    products = getpar_fromtext(example_config_area, 'products')
    prod = vds.products[products]
    assert prod.api_name is not None
    vds.check_valid_products(products)

# EOF
