import astropy
import numpy as np
import pytest
from astropy import units as u
from astropy.utils.introspection import minversion
from astropy.wcs import WCS
from specutils import Spectrum1D
from glue.core.roi import XRangeROI
from glue_astronomy.translators.spectrum1d import PaddedSpectrumWCS
from numpy.testing import assert_allclose, assert_array_equal

from jdaviz.utils import PRIHDR_KEY

ASTROPY_LT_5_3 = not minversion(astropy, "5.3.dev")


@pytest.mark.filterwarnings('ignore')
def test_fits_image_hdu_parse(image_cube_hdu_obj, cubeviz_helper):
    cubeviz_helper.load_data(image_cube_hdu_obj)

    assert len(cubeviz_helper.app.data_collection) == 3
    assert cubeviz_helper.app.data_collection[0].label == "Unknown HDU object[FLUX]"

    # first load should be successful; subsequent attempts should fail
    with pytest.raises(RuntimeError, match="Only one cube"):
        cubeviz_helper.load_data(image_cube_hdu_obj)


@pytest.mark.filterwarnings('ignore')
def test_fits_image_hdu_with_microns(image_cube_hdu_obj_microns, cubeviz_helper):
    # Passing in data_label keyword as posarg.
    cubeviz_helper.load_data(image_cube_hdu_obj_microns, 'has_microns')

    assert len(cubeviz_helper.app.data_collection) == 3
    assert cubeviz_helper.app.data_collection[0].label == 'has_microns[FLUX]'

    flux_cube = cubeviz_helper.app.data_collection[0].get_object(Spectrum1D, statistic=None)
    assert flux_cube.spectral_axis.unit == u.um

    # This tests the same data as test_fits_image_hdu_parse above.

    cubeviz_helper.app.data_collection[0].meta['EXTNAME'] == 'FLUX'
    cubeviz_helper.app.data_collection[1].meta['EXTNAME'] == 'MASK'
    cubeviz_helper.app.data_collection[2].meta['EXTNAME'] == 'ERR'
    for i in range(3):
        assert cubeviz_helper.app.data_collection[i].meta[PRIHDR_KEY]['BITPIX'] == 8

    flux_viewer = cubeviz_helper.app.get_viewer('flux-viewer')
    flux_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': 0, 'y': 0}})
    if ASTROPY_LT_5_3:
        flux_unit_str = "erg / (Angstrom cm2 s)"
    else:
        flux_unit_str = "erg / (Angstrom s cm2)"
    assert flux_viewer.label_mouseover.pixel == 'x=00.0 y=00.0'
    assert flux_viewer.label_mouseover.value == f'+1.00000e+00 1e-17 {flux_unit_str}'

    unc_viewer = cubeviz_helper.app.get_viewer('uncert-viewer')
    unc_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': -1, 'y': 0}})
    assert unc_viewer.label_mouseover.pixel == 'x=-1.0 y=00.0'
    assert unc_viewer.label_mouseover.value == ''  # Out of bounds


def test_spectrum1d_with_fake_fixed_units(spectrum1d, cubeviz_helper):
    header = {
        'WCSAXES': 1,
        'CRPIX1': 0.0,
        'CDELT1': 1E-06,
        'CUNIT1': 'm',
        'CTYPE1': 'WAVE',
        'CRVAL1': 0.0,
        'RADESYS': 'ICRS'}
    wcs = WCS(header)
    cubeviz_helper.app.add_data(spectrum1d, "test")

    dc = cubeviz_helper.app.data_collection
    dc[0].meta["_orig_wcs"] = wcs
    dc[0].meta["_orig_spec"] = spectrum1d

    cubeviz_helper.app.add_data_to_viewer('spectrum-viewer', 'test')
    cubeviz_helper.app.get_viewer('spectrum-viewer').apply_roi(XRangeROI(6600, 7400))

    subsets = cubeviz_helper.app.get_subsets_from_viewer("spectrum-viewer")
    reg = subsets.get('Subset 1')

    assert len(subsets) == 1
    assert_allclose(reg.lower.value, 6666.666666666667)
    assert_allclose(reg.upper.value, 7333.333333333334)
    assert reg.lower.unit == 'Angstrom'
    assert reg.upper.unit == 'Angstrom'


@pytest.mark.filterwarnings('ignore')
def test_fits_image_hdu_parse_from_file(tmpdir, image_cube_hdu_obj, cubeviz_helper):
    f = tmpdir.join("test_fits_image.fits")
    path = f.strpath
    image_cube_hdu_obj.writeto(path, overwrite=True)
    cubeviz_helper.load_data(path)

    assert len(cubeviz_helper.app.data_collection) == 3
    assert cubeviz_helper.app.data_collection[0].label == "test_fits_image.fits[FLUX]"

    # This tests the same data as test_fits_image_hdu_parse above.

    cubeviz_helper.app.data_collection[0].meta['EXTNAME'] == 'FLUX'
    cubeviz_helper.app.data_collection[1].meta['EXTNAME'] == 'MASK'
    cubeviz_helper.app.data_collection[2].meta['EXTNAME'] == 'ERR'
    for i in range(3):
        assert cubeviz_helper.app.data_collection[i].meta[PRIHDR_KEY]['BITPIX'] == 8

    flux_viewer = cubeviz_helper.app.get_viewer(cubeviz_helper._default_flux_viewer_reference_name)
    flux_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': 0, 'y': 0}})
    if ASTROPY_LT_5_3:
        flux_unit_str = "erg / (Angstrom cm2 s)"
    else:
        flux_unit_str = "erg / (Angstrom s cm2)"
    assert flux_viewer.label_mouseover.pixel == 'x=00.0 y=00.0'
    assert flux_viewer.label_mouseover.value == f'+1.00000e+00 1e-17 {flux_unit_str}'
    assert flux_viewer.label_mouseover.world_ra_deg == '205.4433848390'
    assert flux_viewer.label_mouseover.world_dec_deg == '26.9996149270'

    unc_viewer = cubeviz_helper.app.get_viewer(cubeviz_helper._default_uncert_viewer_reference_name)
    unc_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': -1, 'y': 0}})
    assert unc_viewer.label_mouseover.pixel == 'x=-1.0 y=00.0'
    assert unc_viewer.label_mouseover.value == ''  # Out of bounds
    assert unc_viewer.label_mouseover.world_ra_deg == '205.4433848390'
    assert unc_viewer.label_mouseover.world_dec_deg == '26.9996149270'


@pytest.mark.filterwarnings('ignore')
def test_spectrum3d_parse(image_cube_hdu_obj, cubeviz_helper):
    flux = image_cube_hdu_obj[1].data << u.Unit(image_cube_hdu_obj[1].header['BUNIT'])
    wcs = WCS(image_cube_hdu_obj[1].header, image_cube_hdu_obj)
    sc = Spectrum1D(flux=flux, wcs=wcs)
    cubeviz_helper.load_data(sc)

    data = cubeviz_helper.app.data_collection[0]
    assert len(cubeviz_helper.app.data_collection) == 1
    assert data.label == "Unknown spectrum object[FLUX]"
    assert data.shape == flux.shape

    # Same as flux viewer data in test_fits_image_hdu_parse_from_file
    flux_viewer = cubeviz_helper.app.get_viewer(cubeviz_helper._default_flux_viewer_reference_name)
    flux_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': 0, 'y': 0}})
    if ASTROPY_LT_5_3:
        flux_unit_str = "erg / (Angstrom cm2 s)"
    else:
        flux_unit_str = "erg / (Angstrom s cm2)"
    assert flux_viewer.label_mouseover.pixel == 'x=00.0 y=00.0'
    assert flux_viewer.label_mouseover.value == f'+1.00000e+00 1e-17 {flux_unit_str}'
    assert flux_viewer.label_mouseover.world_ra_deg == '205.4433848390'
    assert flux_viewer.label_mouseover.world_dec_deg == '26.9996149270'

    # These viewers have no data.

    unc_viewer = cubeviz_helper.app.get_viewer(cubeviz_helper._default_uncert_viewer_reference_name)
    unc_viewer.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': -1, 'y': 0}})
    assert unc_viewer.label_mouseover is None


def test_spectrum3d_no_wcs_parse(cubeviz_helper):
    sc = Spectrum1D(flux=np.ones(24).reshape((2, 3, 4)) * u.nJy)  # x, y, z
    cubeviz_helper.load_data(sc)
    assert sc.spectral_axis.unit == u.pix

    data = cubeviz_helper.app.data_collection[0]
    flux = data.get_component('flux')
    assert data.label.endswith('[FLUX]')
    assert data.shape == (3, 2, 4)  # y, x, z
    assert isinstance(data.coords, PaddedSpectrumWCS)
    assert_array_equal(flux.data, 1)
    assert flux.units == 'nJy'


def test_spectrum1d_parse(spectrum1d, cubeviz_helper):
    cubeviz_helper.load_data(spectrum1d)

    assert len(cubeviz_helper.app.data_collection) == 1
    assert cubeviz_helper.app.data_collection[0].label.endswith('Spectrum1D')
    assert cubeviz_helper.app.data_collection[0].meta['uncertainty_type'] == 'std'

    # Coordinate display is only for spatial image, which is missing here.
    flux_viewer = cubeviz_helper.app.get_viewer(cubeviz_helper._default_flux_viewer_reference_name)
    assert flux_viewer.label_mouseover is None


def test_numpy_cube(cubeviz_helper):
    arr = np.ones(24).reshape((4, 3, 2))  # x, y, z

    with pytest.raises(TypeError, match='Data type must be one of'):
        cubeviz_helper.load_data(arr, data_type='foo')

    cubeviz_helper.load_data(arr)
    cubeviz_helper.load_data(arr << u.nJy, data_label='uncert_array', data_type='uncert',
                             override_cube_limit=True)

    with pytest.raises(RuntimeError, match='Only one cube'):
        cubeviz_helper.load_data(arr, data_type='mask')

    assert len(cubeviz_helper.app.data_collection) == 2

    # Check context of first cube.
    data = cubeviz_helper.app.data_collection[0]
    flux = data.get_component('flux')
    assert data.label == 'Array'
    assert data.shape == (4, 3, 2)  # x, y, z
    assert isinstance(data.coords, PaddedSpectrumWCS)
    assert flux.units == 'ct'

    # Check context of second cube.
    data = cubeviz_helper.app.data_collection[1]
    flux = data.get_component('flux')
    assert data.label == 'uncert_array'
    assert data.shape == (4, 3, 2)  # x, y, z
    assert isinstance(data.coords, PaddedSpectrumWCS)
    assert flux.units == 'nJy'


def test_invalid_data_types(cubeviz_helper):
    with pytest.raises(FileNotFoundError, match='Could not locate file'):
        cubeviz_helper.load_data('does_not_exist.fits')

    with pytest.raises(NotImplementedError, match='Unsupported data format'):
        cubeviz_helper.load_data(WCS(naxis=3))

    with pytest.raises(NotImplementedError, match='Unsupported data format'):
        cubeviz_helper.load_data(Spectrum1D(flux=np.ones((2, 2)) * u.nJy))

    with pytest.raises(NotImplementedError, match='Unsupported data format'):
        cubeviz_helper.load_data(np.ones((2, 2)))

    with pytest.raises(NotImplementedError, match='Unsupported data format'):
        cubeviz_helper.load_data(np.ones((2, )))
