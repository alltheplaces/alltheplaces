from scrapy.crawler import Crawler

from locations.categories import Categories, apply_category, get_category_tags
from locations.items import Feature
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects():
    class Spider(object):
        pass

    spider = Spider()
    spider.crawler = Crawler(GreggsGBSpider)
    spider.crawler._apply_settings()
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
