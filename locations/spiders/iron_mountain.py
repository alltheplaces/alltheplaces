from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class IronMountainSpider(CrawlSpider, StructuredDataSpider):
    name = "iron_mountain"
    item_attributes = {"brand": "Iron Mountain", "brand_wikidata": "Q1673079"}
    start_urls = ["https://locations.ironmountain.com"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@class="map-list-item-wrap is-single"]')),
        Rule(LinkExtractor(restrict_xpaths='//*[@class="map-list-item is-single"]')),
        Rule(LinkExtractor(restrict_xpaths='//*[@class="locator"]//ul/li/a[1]'), callback="parse_sd"),
    ]
