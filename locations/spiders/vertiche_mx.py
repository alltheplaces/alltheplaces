from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_ES
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VerticheMXSpider(WPStoreLocatorSpider):
    name = "vertiche_mx"
    item_attributes = {"brand": "Vertiche", "brand_wikidata": "Q113215945", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["vertiche.mx"]
    iseadgg_countries_list = ["MX"]
    search_radius = 24
    max_results = 25
    days = DAYS_ES

    def parse_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("address", None)
        yield item
