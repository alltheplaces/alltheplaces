from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class StarbucksINSpider(CrawlSpider, StructuredDataSpider):
    name = "starbucks_in"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    start_urls = ["https://tsb-stores.starbucksindia.net/"]
    rules = [
        Rule(LinkExtractor(allow=r"/Home$"), "parse_sd"),
        Rule(LinkExtractor(allow=r"page=", restrict_xpaths='//*[contains(text(),"Next")]')),
    ]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
