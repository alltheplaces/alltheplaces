from requests_cache import Iterable
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MarcsSpider(CrawlSpider, StructuredDataSpider):
    name = "marcs"
    item_attributes = {"brand": "Marc's", "brand_wikidata": "Q17080259"}
    allowed_domains = ["marcs.com"]
    start_urls = ["https://www.marcs.com/Store-Finder"]
    rules = [Rule(LinkExtractor(allow="store-finder/"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Marc's ")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
