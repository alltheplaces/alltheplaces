from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class JDWetherspoonSpider(CrawlSpider, StructuredDataSpider):
    name = "j_d_wetherspoon"
    item_attributes = {"brand": "Wetherspoon", "brand_wikidata": "Q6109362"}
    allowed_domains = ["www.jdwetherspoon.com"]
    start_urls = ["https://www.jdwetherspoon.com/pubs/all-pubs"]
    rules = [Rule(LinkExtractor(allow="/pubs/all-pubs/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("postcode") and item.get("postcode") in item.get("street_address"):
            item["addr_full"] = item.pop("street_address")
        yield item
