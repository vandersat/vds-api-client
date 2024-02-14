==============
vds-api-client
==============

.. image:: https://badge.fury.io/py/vds-api-client.svg
    :target: https://badge.fury.io/py/vds-api-client


(Command line) interface to download data batches directly from the VanderSat API


Description
===========

- `Installation instructions`_

Using this module, one can get data from the VanderSat API using either:

- `Command Line Interface (CLI)`_
- `Python API`_

Compatible for Linux, Mac and Windows

Python >= 3.6

This package offers an easy interface to the asynchronous endpoints offered by
the `VanderSat API <https://maps.vandersat.com/api/v2/>`_. However, not all available
endpoints can be accessed through this package.

.. _Installation instructions:

Installation
============

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

Installing the client
---------------------

The package can be installed directly from PyPI. Activate your environment and then install with

``$ pip install vds-api-client``

With this activated environment one can access the vds cli with

``$ vds-api``

(If not, your installation did not succeed)


.. _Command Line Interface (CLI):

Command line interface
======================

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

Username / password
~~~~~~~~~~~~~~~~~~~

For each api call using the cli, the credentials need to be supplied.
These can be parsed along with the call by typing them explicitly like:

``$ vds-api -u [username] -p [password] [command]``

However, it is also convenient to store the credentials so they don't have to be
typed each time. `Set the environment variables <https://www.schrodinger.com/kb/1842>`_
``$VDS_USER`` and ``$VDS_PASS``
with the correct values to automatically fill in your credentials.


Planet internal SSO
~~~~~~~~~~~~~~~~~~~

To use Planet SSO get a token using the following procedure

- **Install:**
  ::

    pip install planet-auth-utils

- **Login:**

  Default login: opens browser for authorization and listens locally for callback.

  ::

    plauth oauth login

- **Get Token:**

  ::

     plauth oauth print-access-token

For each api call using the cli, the credentials need to be supplied.
These can be parsed along with the call by typing them explicitly like:

``$ vds-api -t $(plauth oauth print-access-token) [command]``

However, it is also convenient to store the credentials so they don't have to be
typed each time. `Set the environment variable <https://www.schrodinger.com/kb/1842>`_
``$PL_VDS_OAUTH_TOKEN`` with the correct value to automatically fill in your credentials.

This can be done in one step using this command:

``export PL_VDS_OAUTH_TOKEN=$(plauth oauth print-access-token)``

.. note::
   The Token will expire every 3600 seconds. If that happens during a
   session logging in again and re-setting the environment variable will fix it.

.. note::
    **With the envvars set, the credentials don't have to be parsed explicitly anymore thus the syntax reduces to:**

``$ vds-api [command]``

Impersonation
-------------

If a user manages another VanderSat API user account, it can impersonate this user.
Through the CLI this can also be done using the ``--impersonate`` flag. e.g.

``$ vds-api -u manager@company.com -p password --impersonate "user@company.com" [command]``

or when credentials were stored already

``$ vds-api --impersonate "user@company.com" [command]``

Command specific options
------------------------

Use the help function to retrieve all options for the command line interface.

``$ vds-api [command] --help``


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

``$ vds-api ts -p SM-SMAP-LN-DESC_V003_100 -dr 2015-04-01 2019-01-01 -ll 52 4.5 -o tsfold --masked --av_win 35 --backward --clim -t 20 -cov -v``

.. _Python API:

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

Request time-series data using the `products/<api_name>/[point|roi]-time-series` endpoints.

.. code-block:: python

    from vds_api_client import VdsApiV2
    vds = VdsApiV2()

    vds.set_outfold('testdata/csv')  # Created if it does not exist
    vds.gen_time_series_requests(products=['SM-XN_V001_100'],
                                 start_time='2018-01-01', end_time='2018-01-03',
                                 lons=[6.5], lats=[41.5], rois=[527, 811])
    vds.submit_async_requests()
    vds.download_async_files()

    # Get information on the downloaded files
    vds.summary()


Notice that the lons and
lats are given in a list. When multiple points are defined, the latitude and longitude pairs can be added to the
single lists like this:

.. code-block:: python

    lons=[6.5, 7.5], lats=[41.5, 45]

and they will be processed in parallel.

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
    val = vds.get_value('SM-XN_V001_100', '2020-04-01', lon=20.6, lat=40.4)



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

     # ID / DISPLAY # |  # Name #  |   # Area #   |  # Created at #  |       # Description #
    ===============================================================================================
       25009  /  [X]  | Center     | 1.063e+05 ha | 2020-08-16 12:49 | Center pixels
       25010  /  [X]  | Right      | 9.949e+04 ha | 2020-08-16 12:58 | Right side pixels
       25011  /  [X]  | Bottom     | 6.616e+04 ha | 2020-08-16 12:59 | Bottom side pixels
       30596  /  [ ]  | NewName    | 9.140e+03 ha | 2020-09-18 07:19 | Same rectangle

**Filters**

But now, also filters can be applied to select Rois based on a criterium,
and give the corresponding ids:

.. code-block:: python

    rois_filtered = vds.rois.filter(
        min_id=25000, max_id=25020,
        area_min=1e8, area_max=1e9,
        name_regex='Right|Bottom', description_regex='pixels',
        created_before=dt.datetime(2020, 8, 16, 13, 0),
        created_after=dt.datetime(2020, 8, 16, 12, 57),
        display=True)
    print(rois_filtered)
    print(rois_filtered.ids_to_list())

.. parsed-literal::

     # ID / DISPLAY # |  # Name #  |   # Area #   |  # Created at #  |       # Description #
    ===============================================================================================
       25010  /  [X]  | Right      | 9.949e+04 ha | 2020-08-16 12:58 | Right side pixels
       25011  /  [X]  | Bottom     | 6.616e+04 ha | 2020-08-16 12:59 | Bottom side pixels

    [25010, 25011]

**Geometry**

Accessing the geometry is now supported through the geojson property:

.. code-block:: python

    roi = vds.rois[25010]
    geojson = roi.geojson  # Loads geometry from api
    print(geojson)

    {'type': 'MultiPolygon', 'coordinates': [[[[-5.237732, 66.044796], [-5.237732, 66.956952], [-5.018005, 66.956952], [-5.018005, 66.044796], [-5.237732, 66.044796]]]]}


**Updating**

Updating an Roi's metadata is supported through the roi.update method:

.. code-block:: python

    roi = vds.rois[30596]
    roi.update(name='New name', description='New description', display=False)
    print(vds.rois.filter(name_regex='New name'))

.. parsed-literal::

     # ID / DISPLAY # |  # Name #  |   # Area #   |  # Created at #  |       # Description #
    ===============================================================================================
       30596  /  [ ]  | New name   | 9.140e+03 ha | 2020-09-18 07:19 | New description


**Deleting**

Deleting ROIS from your account is supported through the `delete_rois_from_account()` method.
It expects a list of integers, or a filtered Rois instance. Now we can delete our Rois
quite easily like:

.. code-block:: python

    vds.delete_rois_from_account(vds.rois.filter(description_regex='Selection to Delete'))
