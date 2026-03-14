from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ClubMilanesaSpider(WPStoreLocatorSpider):
    name = "club_milanesa"
    item_attributes = {"brand": "Club Milanesa", "brand_wikidata": "Q117324078"}
    allowed_domains = ["elclubdelamilanesa.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.RESTAURANT, item)
        yield item
