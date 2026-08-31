from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TegutDESpider(StructuredDataSpider):
    name = "tegut_de"
    item_attributes = {"brand": "tegut", "brand_wikidata": "Q1547993"}
    allowed_domains = ["www.tegut.com"]
    start_urls = ["https://www.tegut.com/maerkte/maerkteliste.html"]
    wanted_types = ["GroceryStore"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for href in set(response.xpath('//a[contains(@href, "/maerkte/markt/")]/@href').getall()):
            yield response.follow(href, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("image", None)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
