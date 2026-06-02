from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MotrioSpider(Spider):
    name = "motrio"
    item_attributes = {"brand": "Motrio", "brand_wikidata": "Q6918585"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            "https://www.motrio.fr/web2c/establishments/by-location?domain=motrio&longitude=2.3513765&latitude=48.8575475&unit=KM&limitDistance=6000&size={}&page={}".format(
                page_size, page
            )
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for store in data.get("content"):
            store.update(store.pop("billingAddress"))
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            if website := item.get("website"):
                item["website"] = self.repair_website(website)
            item["image"] = store.get("bannerPictureUrl")
            item["facebook"] = store.get("facebookUrl")
            if lat_lon := store.get("location"):
                item["lon"], item["lat"] = lat_lon["coordinates"]
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            item["opening_hours"] = self.parse_opening_hours(store.get("timeTable"))
            yield item
        if not data["last"]:
            yield self.make_request(data["number"] + 1, data["size"])

    def repair_website(self, website: str) -> str | None:
        if any(keyword in website for keyword in ["maps.", "bing.com", "google", "|", "@"]):
            return None

        if website.lower().startswith("http://"):
            website = website.replace("http://", "https://")
        elif "https://" not in website:
            website = "https://" + website
        return website

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, time in rules.items():
            if time in [" ", None, []]:
                continue
            for open_close_time in time:
                opening_hours.add_range(day, open_close_time.get("startAt"), open_close_time.get("endAt"), "%H:%M:%S")
        return opening_hours
