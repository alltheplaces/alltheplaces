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
            item["ref"] = location.get("internal_id")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full", None)
            item["website"] = f'https://rema1000.dk/find-butik-og-abningstider/{item["ref"]}'
            apply_category(Categories.SHOP_SUPERMARKET, item)
            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook_page_url"))

            try:
                item["opening_hours"] = OpeningHours()
                for rule in location.get("opening_hours", []):
                    day = datetime.strptime(rule["date"], "%Y-%m-%d").strftime("%A")
                    if rule["opening_at"] and rule["closing_at"]:
                        open_time = self.calculate_local_time(rule["opening_at"])
                        close_time = self.calculate_local_time(rule["closing_at"])
                        item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
                    else:
                        item["opening_hours"].set_closed(day)
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
            yield item

    def calculate_local_time(self, time_string: str) -> str:
        utc_datetime = datetime.fromisoformat(time_string)
        local_time = utc_datetime.astimezone(ZoneInfo("Europe/Copenhagen"))
        return local_time.strftime("%H:%M")
