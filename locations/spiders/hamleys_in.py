from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.hamleys import HAMLEYS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class HamleysINSpider(CrawlSpider, StructuredDataSpider):
    name = "hamleys_in"
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES
    start_urls = ["https://stores.hamleys.in/"]
    rules = [Rule(LinkExtractor(r"page=\d+$")), Rule(LinkExtractor("/Home"), callback="parse_sd")]
    wanted_types = ["Store"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data):
        item["branch"] = ld_data["alternateName"]

        yield item
