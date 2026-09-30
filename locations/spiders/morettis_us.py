import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class MorettisUSSpider(CamoufoxSpider):
    name = "morettis_us"
    item_attributes = {"brand": "Moretti's"}
    start_urls = ["https://www.morettisrestaurants.com/locations"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//script[contains(text(), "POPMENU_APOLLO_STATE")]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def parse(self, response: Response) -> Iterable[Feature]:
        script = response.xpath('//script[contains(text(), "window.POPMENU_APOLLO_STATE = ")]/text()').get()
        state_json = script.split("window.POPMENU_APOLLO_STATE = ", 1)[1]
        state, _ = json.JSONDecoder().raw_decode(re.sub(r'"\s*\+\s*"', "", state_json))
        for key, location in state.items():
            if not key.startswith("RestaurantLocation:") or not location.get("isLocationEnabled"):
                continue
            if location.get("isLocationClosed") or location.get("country") != "US":
                continue

            item = Feature(
                ref=location["id"],
                branch=location["name"],
                street_address=location["streetAddress"],
                city=location["city"],
                state=location["state"],
                postcode=location["postalCode"],
                country=location["country"],
                lat=location["lat"],
                lon=location["lng"],
                phone=location.get("displayPhone"),
            )
            for link_ref in location["customContentLinks"]:
                link = state[link_ref["__ref"]]
                if link["name"] == "MENU & DETAILS":
                    item["website"] = response.urljoin(link["url"])
                    break

            hours = OpeningHours()
            for range_ref in location["openingRanges"]:
                opening_range = state[range_ref["__ref"]]
                hours.add_days_range(
                    opening_range["days"],
                    self.seconds_to_time(opening_range["openTime"]),
                    self.seconds_to_time(opening_range["closeTime"]),
                )
            item["opening_hours"] = hours
            apply_category(Categories.RESTAURANT, item)
            yield item

    @staticmethod
    def seconds_to_time(seconds: int) -> str:
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}"
