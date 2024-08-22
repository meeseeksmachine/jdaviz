import pytest
from regions import CirclePixelRegion, PixCoord
from jdaviz.core.marks import Lines
from jdaviz.configs.imviz.plugins.parsers import HAS_ROMAN_DATAMODELS


@pytest.mark.skipif(not HAS_ROMAN_DATAMODELS, reason="roman_datamodels is not installed")
def test_previews(rampviz_helper, roman_level_1_ramp):
    rampviz_helper.load_data(roman_level_1_ramp)

    # add subset:
    region = CirclePixelRegion(center=PixCoord(12.5, 15.5), radius=2)
    rampviz_helper.load_regions(region)
    ramp_extr = rampviz_helper.plugins['Ramp Extraction']._obj

    subsets = rampviz_helper.app.get_subsets()
    ramp_cube = rampviz_helper.app.data_collection[0]
    n_groups = ramp_cube.shape[-1]

    assert len(subsets) == 1
    assert 'Subset 1' in subsets

    integration_viewer = rampviz_helper.app.get_viewer('integration-viewer')

    # contains a layer for the default ramp extraction and the subset:
    assert len(integration_viewer.layers) == 2

    # profile viewer x-axis is the group dimension
    assert str(integration_viewer.state.x_att) == 'Pixel Axis 2 [x]'

    # no subset previews should be visible yet:
    assert len([
        mark for mark in integration_viewer.native_marks
        # should be a subclass of Lines, should be visible,
        if mark.visible and isinstance(mark, Lines) and
        # and the default profile is a 1D series with length n_groups:
        len(mark.x) == n_groups
    ]) == 1

    # check that when the plugin is active, there's one ramp profile generated by the
    # plugin per pixel in the subset (if show_subset_preview),
    # plus one live preview (if show_live_preview):
    for show_live_preview in [True, False]:
        for show_subset_preview in [True, False]:
            with ramp_extr.as_active():
                ramp_extr.show_live_preview = show_live_preview
                ramp_extr.show_subset_preview = show_subset_preview
                ramp_extr.aperture_selected = 'Subset 1'

                subset_state = subsets[ramp_extr.aperture_selected][0]['subset_state']
                n_pixels_in_subset = subset_state.to_mask(ramp_cube)[..., 0].sum()

                assert len([
                    mark for mark in integration_viewer.custom_marks
                    if mark.visible and isinstance(mark, Lines) and
                    len(mark.x) == n_groups
                ]) == int(show_subset_preview) * n_pixels_in_subset + int(show_live_preview)