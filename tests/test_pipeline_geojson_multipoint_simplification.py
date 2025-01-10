from scrapy.utils.test import get_crawler

from scrapy import Spider

from locations.items import Feature
from locations.pipelines.geojson_multipoint_simplification import GeoJSONMultiPointSimplificationPipeline


def get_objects():
    spider = Spider(name="test_spider")
    spider.crawler = get_crawler()
    return Feature(), GeoJSONMultiPointSimplificationPipeline(), spider


def test_single_coordinate_multipoint():
    item, pipeline, spider = get_objects()
    item["geometry"] = {"type": "MultiPoint", "coordinates": [[12.34, 56.78]]}
    pipeline.process_item(item, spider)
    assert item["geometry"]["type"] == "Point"
    assert item["geometry"]["coordinates"][0] == 12.34
    assert item["geometry"]["coordinates"][1] == 56.78

def test_multi_coordinate_multipoint():
    item, pipeline, spider = get_objects()
    item["geometry"] = {"type": "MultiPoint", "coordinates": [[12.34, 56.78], [-12.34, -56.78]]}
    pipeline.process_item(item, spider)
    assert item["geometry"]["type"] == "MultiPoint"
    assert len(item["geometry"]["coordinates"]) == 2
    assert item["geometry"]["coordinates"][0][0] == 12.34
    assert item["geometry"]["coordinates"][0][1] == 56.78
    assert item["geometry"]["coordinates"][1][0] == -12.34
    assert item["geometry"]["coordinates"][1][1] == -56.78

def test_undefined_geometry():
    item, pipeline, spider = get_objects()
    pipeline.process_item(item, spider)
    assert item.get("geometry") == None

def test_blank_geometry():
    item, pipeline, spider = get_objects()
    item["geometry"] = None
    pipeline.process_item(item, spider)
    assert item.get("geometry") == None
