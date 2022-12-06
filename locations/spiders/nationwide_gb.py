from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NationwideGB(CrawlSpider, StructuredDataSpider):
    name = "nationwide_gb"
    item_attributes = {"brand": "Nationwide", "brand_wikidata": "Q846735"}
    start_urls = ["https://www.nationwide.co.uk/branches/index.html"]
    rules = [Rule(LinkExtractor(allow=r"/branches/"), callback="parse_sd", follow=True)]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "permanently closed" not in item["name"].lower():
            yield item
