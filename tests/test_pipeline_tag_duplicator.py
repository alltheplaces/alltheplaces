from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline
from locations.pipelines.tag_duplicator import TagDuplicatorPipeline
from locations.spiders.boots_gb import BootsGBSpider


def test_amenity_healthcare_same_value():
    item = Feature()
    pipeline = TagDuplicatorPipeline()

    item.set_tag("amenity", "dentist")
    item = pipeline.process_item(item)
    assert item.get_tag("healthcare") == "dentist"


def test_amenity_healthcare_different_value():
    item = Feature()
    pipeline = TagDuplicatorPipeline()

    item.set_tag("amenity", "doctors")
    item = pipeline.process_item(item)
    assert item.get_tag("healthcare") == "doctor"


def test_branding_and_duplicating():
    item = Feature()
    spider = BootsGBSpider()
    spider.crawler = get_crawler()
    brand_detection = ApplyNSICategoriesPipeline(spider.crawler)
    duplicator_pipeline = TagDuplicatorPipeline()

    item.set_tag("amenity", "pharmacy")
    item["country"] = "GB"
    item.update(spider.item_attributes)
    item = brand_detection.process_item(item)
    assert item.get_tag("nsi_id") is not None
    item = duplicator_pipeline.process_item(item)
    assert item.get_tag("healthcare") == "pharmacy"
