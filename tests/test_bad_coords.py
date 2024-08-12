from scrapy import Spider
from scrapy.utils.test import get_crawler

from locations.items import Feature, get_lat_lon
from locations.pipelines.check_item_properties import CheckItemPropertiesPipeline


def get_objects(lat, lon):
    spider = Spider("test")
    spider.crawler = get_crawler()
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
        CheckItemPropertiesPipeline(),
        spider,
    )


def test_out_of_bounds():
    items, pipeline, spider = get_objects(100000, -100000)
    for item in items:
        pipeline.process_item(item, spider)

        assert item.get("lat") is None
        assert item.get("lon") is None
        assert item.get("geometry") is None


def test_throw_away_null_island():
    items, pipeline, spider = get_objects(0, 0)
    for item in items:
        pipeline.process_item(item, spider)

        assert item.get("lat") is None
        assert item.get("lon") is None
        assert item.get("geometry") is None

    items, pipeline, spider = get_objects(0.123, 0.456)
    for item in items:
        pipeline.process_item(item, spider)

        assert item.get("lat") is None
        assert item.get("lon") is None
        assert item.get("geometry") is None


def test_invalid():
    items, pipeline, spider = get_objects("0", "0")
    for item in items:
        pipeline.process_item(item, spider)

        assert item.get("lat") is None
        assert item.get("lon") is None
        assert item.get("geometry") is None


def test_bad_geometry():
    items, pipeline, spider = get_objects(None, None)
    for item in items:
        pipeline.process_item(item, spider)

        assert item.get("lat") is None
        assert item.get("lon") is None
        assert item.get("geometry") is None


def test_casting():
    items, pipeline, spider = get_objects(int(20), "20.0")
    for item in items:
        pipeline.process_item(item, spider)

        assert get_lat_lon(item) == (20.0, 20.0)
