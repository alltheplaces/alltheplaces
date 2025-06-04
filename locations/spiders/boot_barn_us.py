from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class BootBarnSpider(JSONBlobSpider):
    name = "boot_barn_us"
    item_attributes = {"brand": "Boot Barn", "brand_wikidata": "Q109825187"}
    allowed_domains = ["www.bootbarn.com"]
    start_urls = ["https://www.bootbarn.com/on/demandware.store/Sites-bootbarn_us-Site/default/LocationSearch-GetStoresForGeolocationPositionAjax"]
    locations_key = ["InquiryResult", "data"]
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {
            "Limit": 5000,
            "Offset": 0,
            "Query": "",
            "Source": "StoreLocatorPage",
        }
        yield JsonRequest(url=self.start_urls[0], data=data)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("StoreInfo"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["email"] = "store" + feature["code"] + "@bootbarn.com"
        item["website"] = "https://www.bootbarn.com/stores?StoreID=" + feature["code"]

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["HoursByDay"]:
            if not day_hours["Open"] or "CLOSED" in day_hours["Open"].upper():
                item["opening_hours"].set_closed(day_hours["Day"])
            else:
                item["opening_hours"].add_range(day_hours["Day"], day_hours["Open"], day_hours["Close"], "%I:%M%p")

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
