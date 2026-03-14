from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature, get_lat_lon
from locations.pipelines.check_item_properties import CheckItemPropertiesPipeline


def get_objects(lat, lon):
    crawler = get_crawler(DefaultSpider)
    crawler.spider = crawler._create_spider()
    return (
        [
            Feature(lat=lat, lon=lon),
            Feature(
                geometry={
                    "type": "Point",
                    "coordinates": [lon, lat],
                }
            ),
        ],
        CheckItemPropertiesPipeline(crawler),
    )


def test_out_of_bounds():
    items, pipeline = get_objects(100000, -100000)
    for item in items:
        pipeline.process_item(item)

        assert item.get("lat", None) is None
        assert item.get("lon", None) is None
        assert item.get("geometry", None) is None


def test_throw_away_null_island():
    items, pipeline = get_objects(0, 0)
    for item in items:
        pipeline.process_item(item)

        assert item.get("lat", None) is None
        assert item.get("lon", None) is None
        assert item.get("geometry", None) is None

    items, pipeline = get_objects(0.123, 0.456)
    for item in items:
        pipeline.process_item(item)

        assert item.get("lat", None) is None
        assert item.get("lon", None) is None
        assert item.get("geometry", None) is None


def test_invalid():
    items, pipeline = get_objects("0", "0")
    for item in items:
        pipeline.process_item(item)

        assert item.get("lat", None) is None
        assert item.get("lon", None) is None
        assert item.get("geometry", None) is None


def test_bad_geometry():
    items, pipeline = get_objects(None, None)
    for item in items:
        pipeline.process_item(item)

        assert item.get("lat", None) is None
        assert item.get("lon", None) is None
        assert item.get("geometry", None) is None


def test_casting():
    items, pipeline = get_objects(int(20), "20.0")
    for item in items:
        pipeline.process_item(item)

        assert get_lat_lon(item) == (20.0, 20.0)
