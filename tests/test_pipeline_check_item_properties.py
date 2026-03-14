from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.check_item_properties import CheckItemPropertiesPipeline


def get_objects():
    crawler = get_crawler(DefaultSpider)
    crawler.spider = crawler._create_spider()
    return crawler.spider, CheckItemPropertiesPipeline(crawler)


def test_country_field_check():
    spider, pipeline = get_objects()

    # Official country code
    item = Feature(country="ZA")
    pipeline.process_item(item)
    assert not spider.crawler.stats.get_value("atp/field/country/invalid")

    # So called "User-assigned" country code
    # https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#User-assigned_code_elements
    item = Feature(country="XK")
    pipeline.process_item(item)
    assert not spider.crawler.stats.get_value("atp/field/country/invalid")

    # Country name is not a valid country code
    item = Feature(country="South Africa")
    pipeline.process_item(item)
    assert spider.crawler.stats.get_value("atp/field/country/invalid")

    # Invalid code
    item = Feature(country="00")
    pipeline.process_item(item)
    assert spider.crawler.stats.get_value("atp/field/country/invalid")

    # Turn nan lat and long to invalid geometry
    item = Feature(lat=float("nan"), lon=20.2)
    pipeline.process_item(item)
    assert spider.crawler.stats.get_value("atp/field/geometry/invalid")


def test_geometry_preservation():
    spider, pipeline = get_objects()

    # Point geometry should survive the pipeline
    item = Feature()
    item["geometry"] = {"type": "Point", "coordinates": [6.796508, 61.75317]}
    pipeline.process_item(item)
    assert item.get("geometry") is not None
    assert item["geometry"]["type"] == "Point"
    assert item["geometry"]["coordinates"] == [6.796508, 61.75317]
    assert item.get("lat") is None
    assert item.get("lon") is None

    # LineString geometry should survive the pipeline
    item = Feature()
    item["geometry"] = {
        "type": "LineString",
        "coordinates": [[6.796508, 61.75317], [6.796482, 61.753146], [6.796447, 61.753117]],
    }
    pipeline.process_item(item)
    assert item.get("geometry") is not None
    assert item["geometry"]["type"] == "LineString"
    assert len(item["geometry"]["coordinates"]) == 3
    assert item.get("lat") is None
    assert item.get("lon") is None

    # MultiLineString geometry should survive the pipeline
    item = Feature()
    item["geometry"] = {
        "type": "MultiLineString",
        "coordinates": [
            [[6.0, 61.0], [6.1, 61.1]],
            [[7.0, 62.0], [7.1, 62.1]],
        ],
    }
    pipeline.process_item(item)
    assert item.get("geometry") is not None
    assert item["geometry"]["type"] == "MultiLineString"

    # Polygon geometry should survive the pipeline
    item = Feature()
    item["geometry"] = {
        "type": "Polygon",
        "coordinates": [[[6.0, 61.0], [6.1, 61.0], [6.1, 61.1], [6.0, 61.1], [6.0, 61.0]]],
    }
    pipeline.process_item(item)
    assert item.get("geometry") is not None
    assert item["geometry"]["type"] == "Polygon"


def test_invalid_geometry():
    spider, pipeline = get_objects()

    # Invalid geometry type should be rejected
    item = Feature()
    item["geometry"] = {"type": "InvalidType", "coordinates": []}
    pipeline.process_item(item)
    assert item.get("geometry") is None
    assert spider.crawler.stats.get_value("atp/field/geometry/invalid")

    # Missing geometry type should be rejected
    item = Feature()
    item["geometry"] = {"coordinates": []}
    pipeline.process_item(item)
    assert item.get("geometry") is None
    assert spider.crawler.stats.get_value("atp/field/geometry/invalid")
