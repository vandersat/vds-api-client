import os
import datetime as dt

from vds_api_client.vds_api_base import VdsApiBase, getpar_fromtext
from vds_api_client.types import Rois, Roi, GeoJson


def test_rois_getitem(credentials, example_config_ts):

    vds = VdsApiBase(credentials['user'], credentials['pw'])
    assert isinstance(vds.rois, Rois)
    assert all([isinstance(r, Roi) for r in vds.rois])
    roi_str, roi_name = getpar_fromtext(example_config_ts, 'rois')
    assert vds.rois[roi_str].id == int(roi_str)
    assert vds.rois[int(roi_str)].id == int(roi_str)
    assert vds.rois[roi_name].name == roi_name


def test_rois_filter():

    vds = VdsApiBase()
    rois = vds.rois.filter(min_id=25009, max_id=25010)
    assert rois.ids_to_list() == [25009, 25010]

    rois = vds.rois.filter(area_min=1e8, area_max=1e9)
    assert rois.ids_to_list() == [25010, 25011]

    rois = vds.rois.filter(name_regex='Center|Bottom', description_regex='pixels')
    assert rois.ids_to_list() == [25009, 25011]

    rois = vds.rois.filter(created_after=dt.datetime(2020, 8, 16, 12, 58),
                           created_before=dt.datetime(2020, 8, 16, 13, 0))
    assert rois.ids_to_list() == [25010, 25011]


def test_show_hide_all():

    vds = VdsApiBase()
    vds.rois.show_all()
    assert all([roi.display for roi in vds.rois])

    vds.rois.hide_all()
    assert all([not roi.display for roi in vds.rois])

    vds.rois.filter(max_id=25010).show_all()
    assert vds.rois[25009].display
    assert vds.rois[25010].display
    assert not vds.rois[25011].display


def test_roi_geojson():
    vds = VdsApiBase()
    roi = vds.rois[25009]

    geojson_should = {'type': 'MultiPolygon',
                      'coordinates': [[[[-5.718384, 66.264645],
                                        [-5.718384, 66.739902],
                                        [-5.267944, 66.739902],
                                        [-5.267944, 66.264645],
                                        [-5.718384, 66.264645]]]]
                      }

    assert roi._geojson is None
    requested_geojson = roi.geojson
    assert requested_geojson == geojson_should


def test_roi_update():

    vds = VdsApiBase()
    roi = vds.rois[30596]  # This one is meant to be updated

    roi.update('OldName', description='old rect', display=False)

    assert roi.name == 'OldName'
    assert roi.description == 'old rect'
    assert not roi.display

    roi.update('NewName', description='Same rectangle', display=True)
    assert roi.name == 'NewName'
    assert roi.description == 'Same rectangle'
    assert roi.display


def test_geojson_init():

    geojson_should = (
        '{"type": "FeatureCollection", "features": [{"type": "Feature", "id": "0", '
        '"geometry": {"type": "Polygon", "coordinates": [[[-5.9, 66.2], [-5.8, 66.2], [-5.8, 66.1], '
        '[-5.9, 66.1], [-5.9, 66.2]]]}, "properties": {"id": 30, "name": "lower-left", '
        '"descript": "test shape for the python api client"}}, {"type": "Feature", "id": "1", '
        '"geometry": {"type": "Polygon", "coordinates": [[[-5.85, 66.25], [-5.75, 66.25], '
        '[-5.75, 66.15], [-5.850535, 66.15], [-5.85, 66.25]]]}, "properties": {"id": null, '
        '"name": "shifted", "descript": "shifted test region"}}]}'
    )
    geojson = GeoJson(geojson_should)
    assert str(geojson) == geojson_should

    geojson_dict = {'type': 'FeatureCollection',
                    'features': [{'type': 'Feature', 'id': '0',
                                  'geometry': {'type': 'Polygon', 'coordinates': [
                                      [[-5.9, 66.2], [-5.8, 66.2], [-5.8, 66.1],
                                       [-5.9, 66.1], [-5.9, 66.2]]]},
                                  'properties': {'id': 30, 'name': 'lower-left',
                                                 'descript': 'test shape for the python api client'}},
                                 {'type': 'Feature', 'id': '1',
                                  'geometry': {'type': 'Polygon', 'coordinates': [
                                      [[-5.85, 66.25], [-5.75, 66.25], [-5.75, 66.15],
                                       [-5.850535, 66.15], [-5.85, 66.25]]]},
                                  'properties': {'id': None, 'name': 'shifted',
                                                 'descript': 'shifted test region'}}]}
    geojson = GeoJson(geojson_dict)
    assert str(geojson) == geojson_should


def test_geojson_from_shapefile(testdata_dir):

    geojson_should = (
        '{"type": "FeatureCollection", "features": [{"type": "Feature", "id": "0", '
        '"geometry": {"type": "Polygon", "coordinates": [[[-5.9, 66.2], [-5.8, 66.2], [-5.8, 66.1], '
        '[-5.9, 66.1], [-5.9, 66.2]]]}, "properties": {"id": 30, "name": "lower-left", '
        '"descript": "test shape for the python api client"}}, {"type": "Feature", "id": "1", '
        '"geometry": {"type": "Polygon", "coordinates": [[[-5.85, 66.25], [-5.75, 66.25], '
        '[-5.75, 66.15], [-5.850535, 66.15], [-5.85, 66.25]]]}, "properties": {"id": null, '
        '"name": "shifted", "descript": "shifted test region"}}]}'
    )
    shp_zip = os.path.join(testdata_dir, 'two-rectangles.zip')

    vds = VdsApiBase()  # Necessary for the credentials to be set
    geojson = GeoJson.from_shapefile(shp_zip)
    assert str(geojson) == geojson_should