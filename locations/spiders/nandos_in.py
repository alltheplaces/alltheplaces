from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class NandosINSpider(CrawlSpider, StructuredDataSpider):
    name = "nandos_in"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    start_urls = ["https://www.nandosindia.com/eat/restaurants-all"]
    rules = [Rule(LinkExtractor(allow=r"/eat/restaurant/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["addr_full"] = item.pop("street_address")

        yield item
