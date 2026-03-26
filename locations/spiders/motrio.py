from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MotrioSpider(Spider):
    name = "motrio"
    item_attributes = {"brand": "Motrio", "brand_wikidata": "Q6918585"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            "https://www.motrio.fr/api/establishments?domain=motrio&size={}&page={}".format(page_size, page)
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response):
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
            item["opening_hours"] = OpeningHours()
            for day, time in store.get("timeTable").items():
                if time in [" ", None, []]:
                    continue
                for open_close_time in time:
                    open_time = open_close_time.get("startAt")
                    close_time = open_close_time.get("endAt")
                    item["opening_hours"].add_range(
                        day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                    )
            yield item
        if not data["last"]:
            yield self.make_request(data["number"] + 1, data["size"])

    def repair_website(self, website):
        if any(keyword in website for keyword in ["maps.", "bing.com", "google", "|", "@"]):
            return None

        if website.lower().startswith("http://"):
            website = website.replace("http://", "https://")
        elif "https://" not in website:
            website = "https://" + website
        return website
