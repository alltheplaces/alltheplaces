from locations.exporters.geojson import iter_spider_classes_in_all_modules


def test_item_attributes_type():
    for spider_class in iter_spider_classes_in_all_modules():
        item_attributes = getattr(spider_class, "item_attributes", {})
        assert isinstance(item_attributes, dict)

        if extras := item_attributes.get("extras"):
            assert isinstance(extras, dict)
