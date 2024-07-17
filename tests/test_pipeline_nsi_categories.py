from scrapy import Spider
from scrapy.utils.test import get_crawler

from locations.categories import Categories, apply_category, get_category_tags
from locations.items import Feature
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline


def get_objects():
    spider = Spider(name="test")
    spider.crawler = get_crawler()
    return Feature(), ApplyNSICategoriesPipeline(), spider


def test_no_categories():
    item, pipeline, _ = get_objects()

    assert get_category_tags(item) is None


def test_categories_apply():
    item, pipeline, _ = get_objects()
    apply_category(Categories.BUS_STOP, item)

    assert item["extras"]["highway"] == "bus_stop"
    assert item["extras"]["public_transport"] == "platform"


def test_categories_extract():
    item, pipeline, _ = get_objects()
    apply_category(Categories.BUS_STOP, item)

    assert get_category_tags(item) == Categories.BUS_STOP.value
    assert get_category_tags(Categories.BUS_STOP) == Categories.BUS_STOP.value
    assert get_category_tags(Categories.BUS_STOP.value) == Categories.BUS_STOP.value


def test_categories_filter():
    item, pipeline, _ = get_objects()
    apply_category(Categories.BUS_STOP, item)

    filtered = pipeline.filter_categories(
        [
            {
                "displayName": "test",
                "id": "test_bus_stop",
                "locationSet": {"include": ["001"]},
                "tags": {
                    "highway": "bus_stop",
                    "public_transport": "platform",
                },
            },
            {
                "displayName": "test",
                "id": "test_bus_stop",
                "locationSet": {"include": ["001"]},
                "tags": {
                    "highway": "bus_station",
                    "public_transport": "station",
                },
            },
        ],
        item["extras"],
    )
    assert len(filtered) == 1
    assert filtered[0]["id"] == "test_bus_stop"

    matches = [
        {
            "id": "test_bakery",
            "locationSet": {"include": ["001"]},
            "tags": {
                "shop": "bakery",
            },
        },
        {
            "id": "test_cafe_with_bakery",
            "locationSet": {"include": ["001"]},
            "tags": {
                "shop": "bakery",
                "amenity": "cafe",
            },
        },
    ]

    item, _, _ = get_objects()
    apply_category(Categories.CAFE, item)
    apply_category(Categories.SHOP_BAKERY, item)
    filtered = pipeline.filter_categories(matches, get_category_tags(item))
    assert len(filtered) == 1
    assert filtered[0]["id"] == "test_cafe_with_bakery"

    item, _, _ = get_objects()
    apply_category(Categories.SHOP_BAKERY, item)
    filtered = pipeline.filter_categories(matches, get_category_tags(item))
    assert len(filtered) == 1
    assert filtered[0]["id"] == "test_bakery"

    item, _, _ = get_objects()
    apply_category(Categories.CAFE, item)
    filtered = pipeline.filter_categories(matches, get_category_tags(item))
    assert len(filtered) == 0


def test_cc_filter():
    _, pipeline, _ = get_objects()
    matches = [
        {
            "displayName": "test",
            "id": "test_us",
            "locationSet": {"include": ["US"]},
            "tags": {
                "highway": "bus_stop",
                "public_transport": "platform",
            },
        },
        {
            "displayName": "test",
            "id": "test_global",
            "locationSet": {"include": ["001"]},
            "tags": {
                "highway": "bus_station",
                "public_transport": "station",
            },
        },
    ]

    filtered = pipeline.filter_cc(matches, "US")
    assert len(filtered) == 1
    assert filtered[0]["id"] == "test_us"

    filtered = pipeline.filter_cc(matches, "GB")
    assert len(filtered) == 1
    assert filtered[0]["id"] == "test_global"


def test_nsi_brand_matching():
    item, pipeline, spider = get_objects()
    item["brand_wikidata"] = "Q4683851"
    pipeline.process_item(item, spider)

    assert item["nsi_id"]


def test_nsi_operator_matching():
    item, pipeline, spider = get_objects()
    item["operator_wikidata"] = "Q4829193"
    pipeline.process_item(item, spider)

    assert item["nsi_id"]


def test_filter_cc_considers_already_applied_category():
    item, pipeline, _ = get_objects()
    apply_category(Categories.CAR_RENTAL, item)
    matches = [
        {
            "locationSet": {"include": ["001"]},
            "tags": {
                "amenity": "car_rental",
            },
        },
        {"locationSet": {"include": ["ca", "us"]}, "tags": {"shop": "rental"}},
    ]
    filtered = pipeline.filter_cc(matches, "us", get_category_tags(item))
    assert len(filtered) == 1
    assert filtered[0]["tags"]["amenity"] == "car_rental"

    # For the same matches country specific match should be returned when no category is applied
    _, pipeline, _ = get_objects()
    filtered = pipeline.filter_cc(matches, "us")
    assert len(filtered) == 1
    assert filtered[0]["tags"]["shop"] == "rental"
