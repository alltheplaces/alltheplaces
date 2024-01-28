from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class NandosAESpider(CrawlSpider, StructuredDataSpider):
    name = "nandos_ae"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    start_urls = ["https://www.nandos.ae/eat/restaurants-all"]
    rules = [Rule(LinkExtractor(allow=r"/eat/restaurant/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["addr_full"] = clean_address(item.pop("street_address"))

        yield item
