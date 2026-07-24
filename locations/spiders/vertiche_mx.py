from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_ES
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VerticheMXSpider(WPStoreLocatorSpider):
    name = "vertiche_mx"
    item_attributes = {"brand": "Vertiche", "brand_wikidata": "Q113215945"}
    allowed_domains = ["vertiche.mx"]
    iseadgg_countries_list = ["MX"]
    search_radius = 315
    max_results = 100
    days = DAYS_ES

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        yield item
