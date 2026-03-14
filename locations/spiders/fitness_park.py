from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FitnessParkSpider(Spider):
    name = "fitness_park"
    item_attributes = {"brand": "Fitness Park", "brand_wikidata": "Q102351191"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, offset: int, page_size: int = 50) -> JsonRequest:
        return JsonRequest(
            "https://lesclubs.fitnesspark.fr/search?per={}&offset={}".format(page_size, offset),
            cb_kwargs={"offset": offset, "page_size": page_size},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, offset: int, page_size: int, **kwargs: Any) -> Any:
        data = response.json()["response"]

        for location in data["entities"]:
            if location["profile"].get("closed"):
                continue
            item = DictParser.parse(location["profile"])
            item["ref"] = item["website"] = location["profile"]["c_cTAPageLocale"]["url"]
            item["email"] = location["profile"].get("emails", [None])[0]
            item["phone"] = location["profile"].get("mainPhone", {}).get("number")
            item["facebook"] = location["profile"].get("facebookPageUrl")
            item["lat"] = location["profile"]["yextDisplayCoordinate"]["lat"]
            item["lon"] = location["profile"]["yextDisplayCoordinate"]["long"]
            item["branch"] = (
                item.pop("name")
                .replace("Fitness Park - ", "")
                .replace("Fitness Park A ", "")
                .replace("Fitness Park ", "")
            )
            apply_category(Categories.GYM, item)
            item["opening_hours"] = OpeningHours()
            for rule in location["profile"].get("hours", {}).get("normalHours", []):
                if rule["isClosed"]:
                    continue
                for time in rule["intervals"]:
                    item["opening_hours"].add_range(
                        rule["day"],
                        str(time["start"]).zfill(4),
                        str(time["end"]).zfill(4),
                        time_format="%H%M",
                    )
            yield item

        if data["count"] > offset + page_size:
            yield self.make_request(offset + page_size, page_size)
