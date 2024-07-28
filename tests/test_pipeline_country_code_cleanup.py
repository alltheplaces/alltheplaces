from scrapy.spiders import Spider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.country_code_clean_up import CountryCodeCleanUpPipeline


def get_objects(spider_name):
    spider = Spider(name=spider_name)
    spider.crawler = get_crawler()
    return Feature(), CountryCodeCleanUpPipeline(), spider


def test_handle_empty():
    item, pipeline, spider = get_objects("meaningless")
    pipeline.process_item(item, spider)
    assert not item.get("country")


def test_country_from_spider_name():
    item, pipeline, spider = get_objects("greggs_gb")
    pipeline.process_item(item, spider)
    assert "GB" == item.get("country")
    assert 1 == spider.crawler.stats.get_value("atp/field/country/from_spider_name")


def test_multiple_countries_in_spider_name():
    item, pipeline, spider = get_objects("homebase_gb_ie")
    pipeline.process_item(item, spider)
    assert not item.get("country")


def test_country_from_website_url():
    item, pipeline, spider = get_objects("greggs")
    item["website"] = "https://www.greggs.co.uk/index.html"
    pipeline.process_item(item, spider)
    assert "GB" == item.get("country")
    assert 1 == spider.crawler.stats.get_value("atp/field/country/from_website_url")
