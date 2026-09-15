from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DirkNLSpider(CrawlSpider, StructuredDataSpider):
    name = "dirk_nl"
    item_attributes = {"brand": "Dirk", "brand_wikidata": "Q17502722"}
    start_urls = ["https://www.dirk.nl/winkels/"]
    rules = [Rule(LinkExtractor(allow=r"/winkels/[^/]+/[^/]+$"), "parse")]
    wanted_types = ["GroceryStore"]
    search_for_facebook = False

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # The letters of the Dutch postcode are supplied as "addressRegion".
        address = ld_data["address"]
        if region := address.pop("addressRegion", None):
            address["postalCode"] = "{} {}".format(address["postalCode"], region)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
