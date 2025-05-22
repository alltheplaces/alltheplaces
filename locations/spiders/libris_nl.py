from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LibrisNLSpider(JSONBlobSpider):
    name = "libris_nl"
    item_attributes = {"brand": "Libris", "brand_wikidata": "Q2933427"}
    start_urls = ["https://libris.nl/ShopApi/SearchShops?isMapOverview=false"]
    locations_key = "shops"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        if feature["openHours"]:
            item["opening_hours"].add_ranges_from_string(feature["openHours"], days=DAYS_NL)
        apply_category(Categories.SHOP_BOOKS, item)
        yield item
