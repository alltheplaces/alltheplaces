from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SuitDirectGBSpider(JSONBlobSpider):
    name = "suit_direct_gb"
    item_attributes = {"name": "Suit Direct", "brand": "Suit Direct"}
    allowed_domains = ["www.suitdirect.co.uk"]
    start_urls = ["https://www.suitdirect.co.uk/api/inventory/inventoryGetStoreFilter?countryId=0&cityId=0"]
    locations_key = ["data"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not feature["isActive"]:
            return  # Closed store

        item["ref"] = str(feature["id"])
        item["branch"] = item.pop("name", None)
        item["lat"] = feature["latitude"]
        item["lon"] = feature["longtitude"]  # Note: has invalid spelling for field name
        if slug := feature.get("slug"):
            item["website"] = "https://www.suitdirect.co.uk/store-locator/" + slug

        if hours_html := feature.get("workingHours"):
            hours_str = " ".join(Selector(text=hours_html).xpath("//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_str)

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
