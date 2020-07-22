
import subprocess
import click
import click_datetime as click_dt
import os
import time
from vds_api_client.vds_api_base import VdsApiBase, getpar_fromtext
from vds_api_client.api_v2 import VdsApiV2
setattr(VdsApiV2, '__str__', VdsApiBase.__str__)

vds_user = os.environ.get('VDS_USER', None)
vds_pass = os.environ.get('VDS_PASS', None)

creds = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '/tmp')), 'vds_creds.vds')
if os.path.exists(creds):
    if vds_user is None or vds_pass is None:
        user = getpar_fromtext(creds, 'VDS_USER')
        pas = getpar_fromtext(creds, 'VDS_PASS')
    else:
        os.remove(creds)

vds_user = '$VDS_USER (Not set)' if vds_user is None else vds_user
pass_show = '$VDS_PASS (Not set)' if vds_pass is None else '$VDS_PASS'


def set_win_envar(key, value=''):
    subprocess.check_output('setx {} "{}"'.format(key, value))


def set_linux_envar(key, value=''):
    """
    Function which sets the login credentials in the environment shell files.

    Parameters
    ----------
    key: dict key
        key containing the name of the variable to be set
    value: dict value
        value containing the value of the variable to be set.
        Default is ''
    """
    # Construct list with all the files which will be modified
    home_dir = os.path.expanduser('~')
    list_to_check = [
        os.path.join(home_dir, '.bashrc'),
        os.path.join(home_dir, '.zshrc'),
        os.path.join(home_dir, '.profile')
    ]
    # Loop through list
    for fn in list_to_check:
        if os.path.exists(fn):
            update_shell_file(fn, key, value)

    click.echo('{} has been set in all the environment variable '
               'files.'.format(key))


def update_shell_file(full_path, key, value=''):
    """
    Investigate the specified file, check if the key already exists. If the
    key exists, it will be commented out. Afterwards, the new value is added
    to the environment file.

    Parameters
    ----------
    full_path: str
        string containing the full path to the environment file
    key
        key: dict key
        key containing the name of the variable to be set
    value: dict value
        value containing the value of the variable to be set.
        Default is ''
    """
    key += '='
    with open(full_path, "r") as content:
        fc = content.read()

        if key in fc:
            click.echo('{} is already set in {}: old '
                       'environment value will be commented out.'
                       .format(key[:-1], full_path))
            os.system("sed -e '/{}/ s/^#*/#/' -i {}".format(key, full_path))
            content.close()

    with open(full_path, 'a') as f:
        f.write("export {}'{}'\n".format(key, value))
        f.close()
        click.echo('{} has been set in {}.'.format(key[:-1], full_path))


def download_if_unfinished(api_instance, n_jobs=1):
    """
    Download undownloaded files and terminate execution

    Parameters
    ----------
    api_instance: vds_api_client.VdsApiV2
        VdsApiV2 instance which after initialization has a uuids
        attribute that is either filled or not
    n_jobs: int
    """
    if api_instance.uuids:
        api_instance.download_async_files(n_proc=n_jobs)
        api_instance.summary()
        api_instance.logger.info(' ================== Finished ==================')
        exit(0)


@click.group(short_help='Get data from VdS API')
@click.option('--username', '-u',
              default=vds_user,
              show_default=vds_user)
@click.option('--password', '-p',
              default=vds_pass if vds_pass else pass_show,
              show_default=pass_show)
@click.option('--impersonate', '-i',
              help='User to impersonate')
@click.pass_context
def api(ctx, username, password, impersonate):
    ctx.ensure_object(dict)
    ctx.obj['user'] = username
    ctx.obj['passwd'] = password
    ctx.obj['impersonate'] = impersonate
    pass


@api.command(short_help='test the api response')
@click.pass_context
def test(ctx):
    vds = VdsApiBase(ctx.obj['user'], ctx.obj['passwd'], debug=False)
    if ctx.obj['impersonate']:
        vds.impersonate(ctx.obj['impersonate'])
    for bse in ['maps', 'staging', 'test']:
        vds.base = bse
        start = time.time()
        click.echo(vds)
        bv = vds._get_content('http://{}status/'.format(vds.host))['backend_version']
        click.echo("backend version: {}".format(bv))
        vds.logger.info('API RESPONSE TIME: {:0.4f} seconds'.format(time.time() - start))
        click.echo()
    vds.logger.info(' ================== Finished ==================')


@api.command(short_help='List all info')
@click.option('--all_info', '-a', is_flag=True)
@click.option('--user', '-u', 'user_', is_flag=True)
@click.option('--product_list', '-p', is_flag=True)
@click.option('--roi', '-r', is_flag=True)
@click.pass_context
def info(ctx, all_info, user_, product_list, roi):
    vds = VdsApiBase(ctx.obj['user'], ctx.obj['passwd'], debug=False)
    if ctx.obj['impersonate']:
        vds.impersonate(ctx.obj['impersonate'])
    bv = vds._get_content('http://{}status/'.format(vds.host))['backend_version']
    click.echo("backend version: {}".format(bv))
    if not (user_ or product_list or roi):
        all_info = True

    if user_ or all_info:
        show = ['id', 'name', 'email', 'roles', 'login_count', 'last_login_at']
        x, y = zip(*vds.usr_dict['geojson_area_allowed']['coordinates'][0])
        click.echo('\n######################### USER #########################\n')
        for key in show:
            click.echo('{:>26s} | {} '.format(key, vds.usr_dict[key]))
        click.echo('\n{:>26s} | {} {}'.format('Area extent LON', min(x), max(x)))
        click.echo('{:>26s} | {} {}'.format('Area extent LAT', min(y), max(y)))

    if product_list or all_info:
        head = '\n ## |             # API name #            |         # Name #        \n'
        click.echo('\n############################ PRODUCTS ############################' + head + '='*len(head))
        for i, p in enumerate(vds.products):
            click.echo(' {:02d} | {:35s} | {} '.format(i, p.api_name, p.name))

    if roi or all_info:
        click.echo('\n######################### ROIS #########################')
        click.echo(vds.rois)
        click.echo()
        vds.logger.info(' ================== Finished ==================')


@api.command(short_help='Download gridded data over a range of dates')
@click.option('--config_file', '-c', type=click.Path(exists=True),
              help='Path to configuration file (optional)')
@click.option('--product', '-p', 'products', required=True, multiple=True,
              help='Product to download (call multiple by repeating -p)')
@click.option('--lon_range', '-lo', nargs=2, required=True, type=float, help='Range of longitudes:   min max')
@click.option('--lat_range', '-la', nargs=2, required=True, type=float, help='Range of latitudes:    min max')
@click.option('--date_range', '-dr', nargs=2, type=click_dt.Datetime(format='%Y-%m-%d'),
              help='Start end date for daterange:\nYYYY-MM-DD YYYY-MM-DD')
@click.option('--format', '-f', 'fmt', type=click.Choice(['gtiff', 'netcdf4']), help='File format, default is gtiff')
@click.option('--n_proc', '-n', default=4, type=click.IntRange(1, 8), help='Number of simultaneous calls to the API', show_default=True)
@click.option('--outfold', '-o', help='Path to output the data (created if non-existent)')
@click.option('--zipped', '-z', is_flag=True, default=False, help='Return zip folders with all files included')
@click.option('--verbose/--no-verbose', '-v', default=False, help='Set debug statements on')
@click.pass_context
def grid(ctx, config_file, products, lon_range, lat_range, date_range,
         fmt, n_proc, outfold, zipped, verbose):

    vds = VdsApiV2(ctx.obj['user'], ctx.obj['passwd'], debug=False)
    if ctx.obj['impersonate']:
        vds.impersonate(ctx.obj['impersonate'])
    vds.streamlevel = 10 if verbose else 20
    click.echo(vds)
    if outfold:
        vds.outfold = outfold
    elif config_file:
        of = getpar_fromtext(config_file, 'outfold')
        if of:
            vds.outfold = outfold
    download_if_unfinished(vds, n_jobs=n_proc)
    products = list(products) if products else None
    vds.gen_gridded_data_request(gen_uri=False, config_file=config_file, products=products,
                                 start_date=date_range[0], end_date=date_range[1],
                                 lat_min=(lat_range[0] if lat_range else None), lat_max=(lat_range[1] if lat_range else None),
                                 lon_min=(lon_range[0] if lon_range else None), lon_max=(lon_range[1] if lon_range else None),
                                 file_format=fmt, zipped=zipped, nrequests=n_proc)
    vds.log_config()
    vds.submit_async_requests()
    vds.download_async_files(n_proc=n_proc)
    vds.summary()
    vds.logger.info(' ================== Finished ==================')


@api.command(short_help="Download time-series as csv over points or rois")
@click.option('--config_file', '-c', type=click.Path(exists=True),
              help='Path to configuration file (optional)')
@click.option('--product', '-p', 'products', required=True, multiple=True,
              help='Product to download (call multiple by repeating -p)')
@click.option('--latlon', '-ll', 'latlons', nargs=2, type=float, multiple=True,
              help='Latitude-Longitude, can be multiple -ll')
@click.option('--roi', '-r', 'rois', multiple=True,
              help='Region NAME or ID, can be found in the viewer (call multiple by repeating -r)')
@click.option('--date_range', '-dr', nargs=2,
              help='Start end date for daterange:\nYYYY-MM-DD YYYY-MM-DD')
@click.option('--format', '-f', 'fmt', type=click.Choice(['csv', 'json']), default='csv', show_default=True)
@click.option('--masked', is_flag=True, help='Include masked data in output')
@click.option('--av_win', type=int, help='Add averaging +/- days window column to output')
@click.option('--clim', is_flag=True, help='Include climatology column in output')
@click.option('-t', type=int, help='Rootzone soil moisture parameter (days) (not for streaming)')
@click.option('--outfold', '-o', help='Path to output the data (created if no-existent)')
@click.option('--verbose/--no-verbose', '-v', default=False, help='Set debug statements on')
@click.pass_context
def ts(ctx, config_file, products, latlons, rois, date_range, fmt,
       masked, av_win, clim, t, outfold, verbose):

    vds = VdsApiV2(ctx.obj['user'], ctx.obj['passwd'], debug=False)
    if ctx.obj['impersonate']:
        vds.impersonate(ctx.obj['impersonate'])
    vds.streamlevel = 10 if verbose else 20
    click.echo(vds)
    if outfold:
        vds.outfold = outfold
    elif config_file:
        of = getpar_fromtext(config_file, 'outfold')
        if of:
            vds.outfold = of
    products = list(products) if products else None
    download_if_unfinished(vds, 4)
    lats, lons = map(list, zip(*latlons)) if latlons else (None, None)
    rois = list(rois) if rois else None
    vds.gen_time_series_requests(gen_uri=False, config_file=config_file, products=products,
                                 start_time=date_range[0] if date_range else None,
                                 end_time=date_range[1] if date_range else None,
                                 lats=lats, lons=lons, rois=rois,
                                 av_win=av_win, masked=masked, clim=clim, t=t,
                                 file_format=fmt)
    vds.log_config()
    vds.submit_async_requests()
    vds.download_async_files(n_proc=8)
    vds.summary()
    vds.logger.info(' ================== Finished ==================')


if __name__ == '__main__':
    api()

# EOF
