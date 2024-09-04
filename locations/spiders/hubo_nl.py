from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HuboNLSpider(JSONBlobSpider):
    name = "hubo_nl"
    item_attributes = {"brand": "Hubo", "brand_wikidata": "Q5473953", "extras": Categories.SHOP_DOITYOURSELF.value}
    allowed_domains = ["www.hubo.nl"]
    start_urls = ["https://www.hubo.nl/api/storelocator/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["title"]
        item.pop("name", None)
        item["lat"] = feature["address_data"]["location_lat"]
        item["lon"] = feature["address_data"]["location_lng"]
        item["street_address"] = feature["address_data"]["address"]
        item["city"] = feature["address_data"]["city"]
        item["postcode"] = feature["address_data"]["postal_code"]
        item["phone"] = feature["address_data"]["phone_number"]

        if feature.get("url"):
            item["website"] = "https://www.hubo.nl" + feature["url"]

        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in feature.get("opening_hours", {}).items():
            if day_name.title() not in DAYS_FULL:
                continue
            if isinstance(day_hours, dict):
                item["opening_hours"].add_range(day_name.title(), day_hours["from"], day_hours["until"])
            elif day_hours == "Gesloten":  # Closed
                item["opening_hours"].set_closed(DAYS_EN[day_name.title()])

        yield item
