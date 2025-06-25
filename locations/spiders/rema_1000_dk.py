from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media


class Rema1000DKSpider(Spider):
    name = "rema_1000_dk"
    item_attributes = {"brand": "Rema 1000", "brand_wikidata": "Q28459"}
    start_urls = ["https://cphapp.rema1000.dk/api/v3/stores?per_page=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item["ref"] = location.get("internal_id")
            item["branch"] = item.pop("name")
            item["website"] = "https://rema1000.dk/find-butik-og-abningstider/{}".format(item["ref"])
            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook_page_url"))

            apply_category(Categories.SHOP_SUPERMARKET, item)

            try:
                item["opening_hours"] = self.parse_opening_hours(location.get("opening_hours", []))
            except:
                self.logger.error("Error paring opening hours: {}".format(location.get("opening_hours", [])))

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = datetime.strptime(rule["date"], "%Y-%m-%d").strftime("%A")
            if rule["label"] == "Lukket":
                oh.set_closed(day)
            elif rule["opening_at"] and rule["closing_at"]:
                oh.add_range(
                    day, self.calculate_local_time(rule["opening_at"]), self.calculate_local_time(rule["closing_at"])
                )
        return oh

    def calculate_local_time(self, time_string: str) -> str:
        utc_datetime = datetime.fromisoformat(time_string)
        local_time = utc_datetime.astimezone(ZoneInfo("Europe/Copenhagen"))
        return local_time.strftime("%H:%M")
