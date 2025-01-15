from scrapy import Spider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.check_item_properties import CheckItemPropertiesPipeline


def get_spider() -> Spider:
    spider = Spider(name="test")
    spider.crawler = get_crawler()
    return spider


def test_country_field_check():
    pipeline = CheckItemPropertiesPipeline()

    # Official country code
    item = Feature(country="ZA")
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert not spider.crawler.stats.get_value("atp/field/country/invalid")

    # So called "User-assigned" country code
    # https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#User-assigned_code_elements
    item = Feature(country="XK")
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert not spider.crawler.stats.get_value("atp/field/country/invalid")

    # Country name is not a valid country code
    item = Feature(country="South Africa")
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert spider.crawler.stats.get_value("atp/field/country/invalid")

    # Invalid code
    item = Feature(country="00")
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert spider.crawler.stats.get_value("atp/field/country/invalid")
