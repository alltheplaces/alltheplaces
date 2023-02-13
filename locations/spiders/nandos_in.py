from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.nandos import NandosSpider
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class NandosINSpider(CrawlSpider, StructuredDataSpider):
    name = "nandos_in"
    item_attributes = NandosSpider.item_attributes
    start_urls = ["https://www.nandosindia.com/eat/restaurants-all"]
    rules = [Rule(LinkExtractor(allow=r"/eat/restaurant/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = clean_address(item.pop("street_address"))

        yield item
