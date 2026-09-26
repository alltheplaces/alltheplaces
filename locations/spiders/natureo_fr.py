from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FR
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class NatureoFRSpider(WPStoreLocatorSpider):
    name = "natureo_fr"
    item_attributes = {"brand": "naturéO", "brand_wikidata": "Q6981018"}
    allowed_domains = ["www.natureo-bio.fr"]
    days = DAYS_FR
    drop_attributes = {"email"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        # "url" is sometimes the homepage; permalink is always the store page.
        item["website"] = feature["permalink"]
        yield item
