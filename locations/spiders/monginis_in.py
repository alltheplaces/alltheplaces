from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MonginisINSpider(CrawlSpider, StructuredDataSpider):
    name = "monginis_in"
    item_attributes = {"brand": "Monginis", "brand_wikidata": "Q6899504"}
    start_urls = ["https://cakeshops.monginis.net/"]
    rules = [
        Rule(LinkExtractor(allow=(r"/?page=\d+$"))),
        Rule(LinkExtractor(allow=(r"-\d+/Home$")), callback="parse_sd"),
    ]
    wanted_types = ["Bakery"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
