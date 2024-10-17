from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaSalsaUSSpider(CrawlSpider, StructuredDataSpider):
    name = "la_salsa_us"
    item_attributes = {"brand": "La Salsa", "brand_wikidata": "Q48835190"}
    start_urls = ["https://www.lasalsa.com/locator/index.php?brand=26&pagesize=1000&q=us"]
    rules = [
        Rule(LinkExtractor(allow="/stores/"), callback="parse_sd"),
    ]

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["openingHours"] = None  # Requires fix, only a few locations, not worth the effort

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = item.pop("name").removeprefix("La Salsa Store ")
        yield item
