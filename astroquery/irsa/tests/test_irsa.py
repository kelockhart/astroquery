# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import requests

from astropy.tests.helper import pytest
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from ... import irsa
from ...irsa import ROW_LIMIT

DATA_FILES = {'Cone' : 'Cone.xml',
              'Box' : 'Box.xml',
              'Polygon' :  'Polygon.xml'}

OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s", coord.GalacticCoordinates(l=121.1743, b=-21.5733, unit=(u.deg, u.deg))]

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES[params['spatial']])
    content = open(filename, 'r').read()
    return MockResponse(content)

class MockResponse(object):
    def __init__(self, content):
        self.content = content

@pytest.mark.parametrize(('dim'), ['5d0m0s', 0.3 * u.rad, '5h0m0s', 2 * u.arcmin])
def test_parse_dimension(dim):
    # check that the returned dimension is always in units of 'arcsec', 'arcmin' or 'deg'
    new_dim = irsa.core._parse_dimension(dim)
    assert new_dim.unit in ['arcsec', 'arcmin', 'deg']

@pytest.mark.parametrize(('ra', 'dec', 'expected'),
                         [(10, 10, '10 10'),
                          (10.0, -11, '10.0-11')
                          ])
def  test_format_coords(ra, dec, expected):
    out = irsa.core._format_coords(ra, dec)
    assert out == expected

@pytest.mark.parametrize(('coordinates', 'expected'),
                         [("5h0m0s 0d0m0s", "75.0 0.0")
                          ])
def test_parse_coordinates(coordinates, expected):
    out = irsa.core._parse_coordinates(coordinates)
    assert out == expected

@pytest.mark.parametrize(('coordinates', 'expected'),
                         [("5h0m0s 0d0m0s", True),
                          ("m1", False)
                          ])
def test_is_coordinate(coordinates, expected):
    out = irsa.core._is_coordinate(coordinates)
    assert out == expected

def test_args_to_payload():
    out  = irsa.core.Irsa._args_to_payload("fp_psc", "Cone")
    assert out == dict(catalog='fp_psc', spatial='Cone', outfmt=3, outrows=ROW_LIMIT())

@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_cone_async(coordinates, patch_get):
    response = irsa.core.Irsa.query_region_async(coordinates, catalog='fp_psc', spatial='Cone',
                                                 radius=2 * u.arcmin, get_query_payload=True)
    assert response['radius'] == 2
    assert response['radunits'] == 'arcmin'
    response = irsa.core.Irsa.query_region_async(coordinates, catalog='fp_psc', spatial='Cone',
                                                 radius=2 * u.arcmin)
    assert response is not None

@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_cone(coordinates, patch_get):
    result = irsa.core.Irsa.query_region(coordinates, catalog='fp_psc', spatial='Cone',
                                                 radius=2 * u.arcmin)
    assert isinstance(result, Table)
@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_box_async(coordinates, patch_get):
    response = irsa.core.Irsa.query_region_async(coordinates, catalog='fp_psc', spatial='Box',
                                                 width=2 * u.arcmin, get_query_payload=True)
    assert response['size'] == 120
    response = irsa.core.Irsa.query_region_async(coordinates, catalog='fp_psc', spatial='Box',
                                                 width=2 * u.arcmin)
    assert response is not None

@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_box(coordinates, patch_get):
    result = irsa.core.Irsa.query_region(coordinates, catalog='fp_psc', spatial='Box',
                                         width=2 * u.arcmin)
    assert(result, Table)

@pytest.mark.parametrize(("polygon"),
                         [[coord.ICRSCoordinates(ra=10.1, dec=10.1, unit=(u.deg, u.deg)),
                           coord.ICRSCoordinates(ra=10.0, dec=10.1, unit=(u.deg, u.deg)),
                           coord.ICRSCoordinates(ra=10.0, dec=10.0, unit=(u.deg, u.deg))],
                          [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
                          ])
def test_query_region_async_polygon(polygon, patch_get):
    response = irsa.core.Irsa.query_region_async("m31", catalog="fp_psc", spatial="Polygon",
                                                 polygon=polygon, get_query_payload=True)
    assert response["polygon"] == "10.1 10.1,10.0 10.1,10.0 10.0"
    response = irsa.core.Irsa.query_region_async("m31", catalog="fp_psc", spatial="Polygon",
                                                 polygon=polygon)
    assert response is not None

@pytest.mark.parametrize(("polygon"),
                         [[coord.ICRSCoordinates(ra=10.1, dec=10.1, unit=(u.deg, u.deg)),
                           coord.ICRSCoordinates(ra=10.0, dec=10.1, unit=(u.deg, u.deg)),
                           coord.ICRSCoordinates(ra=10.0, dec=10.0, unit=(u.deg, u.deg))],
                          [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
                          ])
def test_query_region_polygon(polygon, patch_get):
    result = irsa.core.Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
                                                 polygon=polygon)
    assert isinstance(result, Table)