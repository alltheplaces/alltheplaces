from locations.exporters.geojson import iter_spider_classes_in_modules


def test_all_spiders_importable():
    """Ensure all spider modules can be imported without errors.

    This catches broken cross-spider dependencies, e.g. when a spider
    is removed but another spider still imports from it.
    """
    spiders = list(iter_spider_classes_in_modules())
    assert len(spiders) > 0
