from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class IntersportFISpider(CrawlSpider, StructuredDataSpider):
    name = "intersport_fi"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.fi/fi/kaupat/"]
    rules = (Rule(LinkExtractor(restrict_xpaths='//a[@data-link="openStorePage"]'), callback="parse_sd"),)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = item["lon"], item["lat"]
        yield item
