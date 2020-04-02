==============
vds_api_client
==============


(Command line) interface to download data batches directly from the VanderSat API


Description
===========

Using this module, one can get data from the VanderSat API using either:

- Command line
- Python console

Compatible for Linux, Mac and Windows
Python >3.6

This package offers an easy interface to the asynchronous endpoints offered by
the `VanderSat API <https://maps.vandersat.com/api/v2/>`_. However, not all available
endpoints can be accessed through this package.

Required packages
-------------------------------------

* click
* requests
* pandas
* click_datetime
* joblib

Setting up an environment
-------------------------
If you don't have an environment yet or would like a new one, use the following line to make a new one using `conda <https://docs.conda.io/en/latest/>`_

    ``$ conda create -n vds_api -c conda-forge python=3 requests "click>=7" pandas joblib pip``

activate it

    ``$ conda activate vds_api``

and follow the installation steps

Installation
------------

The package can be installed directly from PyPI. Activate your environment and then install with

    ``$ pip install vds_api_client``

With this activated environment one can access the vds cli with

    ``$ vds-api``

(If not, your installation did not succeed)


Available CLI commands
----------------------------------------------

    ``$ vds-api``

will show all available commands which should include:

* ``grid`` - download gridded data
* ``info`` - Show info for this account
* ``test`` - test connection, credentials and if api is operational
* ``ts`` - download time-series as csv over points or rois


Calling any of these commands should be done after suppliying credentials:

    ``$ vds api -u [username] -p [password] [command]``

And it is always a good idea to start with a test:

    ``$ vds-api -u [username] -p [password] test``


Credentials
-----------
For each api call using the cli, the credentials need to be supplied.
These can be parsed along with the call by typing them explicitly like:

    ``$ vds-api -u [username] -p [password] [command]``

However, it is also convenient to store the credentials so they don't have to be
typed each time. `Set the environment variables <https://www.schrodinger.com/kb/1842>`_
``$VDS_USER`` and ``$VDS_PASS``
with the correct values to automatically fill in your credentials.

.. note::
    **From this point on, the credentials don't have to be parsed explicitly anymore thus the syntax reduces to:**

    ``$ vds-api [command]``

Impersonation
-------------

If a user manages another VanderSat API user account, it can impersonate this user.
Through the CLI this can also be done using the ``--impersonate`` flag. e.g.

    ``$ vds-api -u manager@company.com -p password --impersonate "user@company.com" [command]``

or when credentials were stored already

    ``$ vds-api --impersonate "user@company.com" [command]``


Command specifications: ``info``
----------------------------------------------

Get a summary of all user information. The shown information contains the following:

* registred user information (name, email, role, etc)
* registred products (api-name | product-name)
* roi information

All info is shown by default but it is also possible to only show part of it with the following options:

-u, --user           show user info
-p, --product_list   show product-list
-r, --roi            show roi info

E.g. to show all available products, type:

    ``$ vds-api info -p``

Command specifications: ``grid``
----------------------------------------------
Get one or multiple gridded data files in GeoTIFF or NetCDF.

See all available options by typing:

    ``$ vds-api grid --help``

Required options:

-p, --product      ``str`` // Product api-Name to download,
                   you can specify multiple products by repeating the ``-p`` flag
-lo, --lon_range   ``float float`` // Range of longitudes, ``-lo min max``
-la, --lat_range   ``float float`` // Range of latitudes, ``-la min max``
-dr, --date_range   ``yyyy-mm-dd yyyy-mm-dd`` // date range to download separated by a space

Optional options:

-f, --format       [``gtiff|netcdf4``] // File format to download, defaults to gtiff
-n, --n_proc       ``int`` // Number of simultaneous calls to the server (default 4, pref <= 8)
-o, --outfold      ``str`` // Path to output the data to (created if it does not exist)
-v, --verbose      Switch to increase the output messages
-c, --config_file  ``str`` // Path to condiguration file containing pre-defined parameters
-z, --zipped       Switch to request the data zipped (if ``n_procs > 1``,
                   multiple zip files will be received)

Command specifications: ``ts``
----------------------------------------------
Get one or multiple csv files with time-series.

See all available options by typing:

    ``$ vds-api ts --help``

Required options:

-p, --product      ``str`` // Product api-Name to download,
                   you can specify multiple products by repeating the ``-p`` flag
-dr, --date_range   ``yyyy-mm-dd yyyy-mm-dd`` // date range to download separated by a space

At least one of the following (yet multiple allowed):

-ll, --latlon  ``float float`` // Latitude-Longitude pair to extract ts, can be multiple by repeating -ll
-r, --roi      ``int`` // Region of interest id that can be referenced at maps.vandersat.com. Repeat -r for multiple

Optional options:

-f, --format       [``csv|json``] // File format to download, defaults to csv
--masked           Switch to also download flagged data
--av_win           ``int`` // Add averaging +/- days window column to output (supply full window)
--clim             Switch to include climatology column in output
-t                 ``int`` // Rootzone soil moisture parameter (days) (not used with streaming)
-v, --verbose      Switch to increase the output messages
-c, --config_file  text // Path to condiguration file containing pre-defined parameters
-o, --outfold      ``str`` // Path to output the data to (created if it does not exist)


V2 CLI Examples
===============

Example usage CLI V2 grid
----------------------------------------------
Get L-band for one month over NL in geotiff with 8 threads

    ``$ vds-api grid -p SM-SMAP-LN-DESC_V003_100 -dr 2015-04-01 2015-04-30 -lo 3 8 -la 50 54 -o SM_L_Data -n 8 -v``

Get L+C+X-band for two dates over NL in netcdf

    ``$ vds-api grid -p SM-SMAP-LN-DESC_V003_100 -p SM-AMSR2-C1N-DESC_V003_100 -p SM-AMSR2-XN_V003_100 -f netcdf4 -dr 2016-07-01 2016-07-02 -lo 3.0 8.0 -la 50.0 54.0 -o NCData -v``

Example usage CLI V2 ts
----------------------------------------------

Get L-band time-series for a region-of-interest (roi) and a lat-lon pair

    ``$ vds-api ts -p SM-SMAP-LN-DESC_V003_100 -dr 2015-05-01 2020-01-01 -ll 52 4.5 -r 3249 -o tsfold -v``

Get time-series with all additional columns

    ``$ vds-api ts -p SM-SMAP-LN-DESC_V003_100 -dr 2015-04-01 2019-01-01 -ll 52 4.5 -o tsfold --masked --av_win 35 --clim -t 20 -v``


Example usage Python API
=========================

Asynchronous requests can easily be downloaded using the ``VdsApiV2`` class.
For downloading of the desired files, the following steps need to be taken:

API v2
------
For the version 2 api, three steps have to be taken to download data from the api which are all methods of the ``VdsApiV2`` class:
 1. Generate a request
        Configure gridded data download or time-series download
        through one of ``gen_time_series_requests()`` or ``gen_gridded_data_request()``
 2. Submit request
        After generating all desired URIs, submit these with ``submit_async_requests()``
        to start the processing of these jobs
 3. Download files
        Get all data using ``download_async_files()``

**Initialize class**

.. code-block:: python

    from vds_api_client import VdsApiV2

    # Choose one of the following options to initialize
    vds = VdsApiV2('username', 'password')
    vds = VdsApiV2()  # extract login from $VDS_USER and $VDS_PASS


**Impersonate user**

When a user manages another account, it can impersonate this managed acount
which means that all requests will be done as if the impersonated user has made them

.. code-block:: python

    vds = VdsApiV2('manager@company.com', 'password')

    # Start impersonation
    vds.impersonate('user@company.com')

    # do_requests

    # End impersonation
    vds.forget()

**Gridded data example [asynchronous]**

Request raster data using the `products/<api_name>/gridded-data` endpoint

.. code-block:: python

    from vds_api_client import VdsApiV2

    vds = VdsApiV2()

    vds.set_outfold('testdata/tiff')  # Created if it does not exist
    vds.gen_gridded_data_request(products=['SM-SMAP-LN-DESC_V003_100', 'SM-AMSR2-XN-DESC_V003_100'],
                                 start_date='2015-10-01', end_date='2016-09-30',
                                 lat_min=-3.15, lat_max=-1.5, lon_min=105, lon_max=107,
                                 nrequests=4)
    vds.submit_async_requests()
    vds.download_async_files()

    # Get information on the downloaded files
    vds.summary()

**Time-series example [asynchronous]**

Request time-series data using the `products/<api_name>/[point|roi]-time-series` endpoints

.. code-block:: python

    from vds_api_client import VdsApiV2
    vds = VdsApiV2()

    vds.set_outfold('testdata/csv')  # Created if it does not exist
    vds.gen_time_series_requests(products=['SM-XN_V001_100'],
                                 start_time='2018-01-01', end_time='2018-01-03',
                                 lons=[6.5], lats=[41.5], rois=[527, 811])
    vds.submit_asynch_requests()
    vds.download_async_files()

    # Get information on the downloaded files
    vds.summary()


**Re-download previous requests**

Re-download data using previously generated uuids. Note that data is not stored indefinitely,
but within 7 days you should be able to re-download your data.

.. code-block:: python

    from vds_api_client import VdsApiV2
    vds = VdsApiV2()

    # Choose from
    vds.uuids.append('5742540a-cf87-49dd-a6e7-d484de137324')
    vds.queue_uuids_files()
    # or
    vds.queue_uuids_files(uuids=['57f9950a-4e41-49dd-a6e7-d484de137324'])


**Get a single point value**

Extract a single value based on a product-coordinate using the `products/<api-name>/point-value`
endpoint

.. code-block:: python

    from vds_api_client import VdsApiV2

    vds = VdsApiV2()

    # Load using the roi-id
    val = vds.get_value('SM-XN_V001_100', '2020-04-01', lon=20.6, 40.4)



**Load Roi time-series as pandas dataframe [synchronous]**

Request roi time-series data using the `products/<api_name>/roi-time-series-sync` endpoint
and load the result as a pandas.DataFrame

.. code-block:: python

    from vds_api_client import VdsApiV2

    vds = VdsApiV2()

    # Load using the roi-id
    df1 = vds.get_roi_df('SM-XN_V001_100', 2464, '2016-01-01', '2018-12-31')

    # Load using the roi-name
    df2 = vds.get_roi_df('SM-XN_V001_100', 'MyArea', '2016-01-01', '2018-12-31')

ROIS
------

Knowing and using the regions of interest (rois) attached to your account is now
easier using the client methods that allow you to filter the rois.

.. code-block:: python

    from vds_api_client import VdsApiV2

    vds = VdsApiV2()

    print(vds.rois)

.. parsed-literal::
     # ID # |       # Name #       |   # Area #   |       # Description #
    ============================================================================
       3249 | GH                   | 3.227e+04 ha | Groene hart cirkel
       3970 | Luxemburg            | 2.593e+05 ha | Administrative Country Boundary
       7046 | Ernange              | 7.244e+02 ha | Ernange area for Kisters / SPW
       9211 | Delete This          | 4.128e+04 ha | Selection to Delete
       9212 | Delete also this one | 7.387e+04 ha | Selection to Delete

But now, also filters can be applied to select Rois based on a criterium,
and give the corresponding ids:

.. code-block:: python

    rois_filtered = vds.rois.filter(min_id=100,
                                    area_min=200,
                                    description_regex='Delete')
    print(rois_filtered)
    print(rois_filtered.ids_to_list())

.. parsed-literal::

    # ID # |       # Name #       |   # Area #   |       # Description #
    ============================================================================
      9211 | Delete This          | 4.128e+04 ha | Selection to Delete
      9212 | Delete also this one | 7.387e+04 ha | Selection to Delete

    [9211, 9212]

Deleting ROIS from your account is supported through the `delete_rois_from_account()` method.
It expects a list of integers, or a filtered Rois instance. Now we can delete our Rois
quite easily like:

.. code-block:: python

    vds.delete_rois_from_account(vds.rois.filter(description_regex='Selection to Delete'))