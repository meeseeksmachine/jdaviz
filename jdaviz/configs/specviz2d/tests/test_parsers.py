import pytest
from asdf.asdf import AsdfWarning
from astropy.utils.data import download_file

from jdaviz.utils import PRIHDR_KEY


@pytest.mark.remote_data
def test_2d_parser_jwst(specviz2d_helper):
    fn = download_file('https://stsci.box.com/shared/static/exnkul627fcuhy5akf2gswytud5tazmw.fits', cache=True)  # noqa

    with pytest.warns(AsdfWarning, match='jwextension'):
        specviz2d_helper.load_data(spectrum_2d=fn)
    assert len(specviz2d_helper.app.data_collection) == 2

    dc_0 = specviz2d_helper.app.data_collection[0]
    assert dc_0.label == 'Spectrum 2D'
    assert PRIHDR_KEY not in dc_0.meta
    assert 'header' not in dc_0.meta
    assert dc_0.meta['DETECTOR'] == 'MIRIMAGE'
    assert dc_0.get_component('flux').units == 'MJy / sr'

    dc_1 = specviz2d_helper.app.data_collection[1]
    assert dc_1.label == 'Spectrum 1D'
    assert 'header' not in dc_1.meta

    # TODO: Update this when specreduce is fixed.
    assert dc_1.get_component('flux').units == 'DN'

    # Also check the coordinates info panel.
    viewer_2d = specviz2d_helper.app.get_viewer('spectrum-2d-viewer')
    viewer_2d.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': 350, 'y': 30}})
    assert viewer_2d.label_mouseover.pixel == 'x=0350.0 y=0030.0'
    assert viewer_2d.label_mouseover.value == '+3.22142e+04 MJy / sr'
    assert viewer_2d.label_mouseover.world_ra_deg == ''
    assert viewer_2d.label_mouseover.world_dec_deg == ''


def test_2d_parser_no_unit(specviz2d_helper, mos_spectrum2d):
    specviz2d_helper.load_data(mos_spectrum2d, spectrum_2d_label='my_2d_spec')
    assert len(specviz2d_helper.app.data_collection) == 2

    dc_0 = specviz2d_helper.app.data_collection[0]
    assert dc_0.label == 'my_2d_spec 2D'
    assert dc_0.get_component('flux').units == ''

    dc_1 = specviz2d_helper.app.data_collection[1]
    assert dc_1.label == 'Spectrum 1D'
    assert dc_1.get_component('flux').units == 'DN'

    # Also check the coordinates info panel.
    viewer_2d = specviz2d_helper.app.get_viewer('spectrum-2d-viewer')
    viewer_2d.on_mouse_or_key_event({'event': 'mousemove', 'domain': {'x': 0, 'y': 0}})
    assert viewer_2d.label_mouseover.pixel == 'x=00000.0 y=00000.0'
    assert viewer_2d.label_mouseover.value == '+3.74540e-01 '
    assert viewer_2d.label_mouseover.world_ra_deg == ''
    assert viewer_2d.label_mouseover.world_dec_deg == ''


def test_1d_parser(specviz2d_helper, spectrum1d):
    specviz2d_helper.load_data(spectrum_1d=spectrum1d)
    assert len(specviz2d_helper.app.data_collection) == 1
    dc_0 = specviz2d_helper.app.data_collection[0]
    assert dc_0.label == 'Spectrum 1D'
    assert dc_0.meta['uncertainty_type'] == 'std'


def test_2d_1d_parser(specviz2d_helper, mos_spectrum2d, spectrum1d):
    specviz2d_helper.load_data(spectrum_2d=mos_spectrum2d, spectrum_1d=spectrum1d)
    assert specviz2d_helper.app.data_collection.labels == ['Spectrum 2D', 'Spectrum 1D']


def test_parser_no_data(specviz2d_helper):
    with pytest.raises(ValueError, match='Must provide spectrum_2d or spectrum_1d'):
        specviz2d_helper.load_data()
