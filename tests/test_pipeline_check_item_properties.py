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
