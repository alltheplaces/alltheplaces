import json
import re
from typing import Any, Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class JonSmithSubsUSSpider(CamoufoxSpider):
    name = "jon_smith_subs_us"
    item_attributes = {"brand": "Jon Smith Subs"}
    allowed_domains = ["jonsmithsubs.com"]
    start_urls = ["https://www.jonsmithsubs.com/locations"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//script[contains(text(), "POPMENU_APOLLO_STATE")]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        script = response.xpath('//script[contains(text(), "POPMENU_APOLLO_STATE")]/text()').get()
        if not script:
            return

        state_json = script.split("window.POPMENU_APOLLO_STATE = ", 1)[1].split("window.__POPMENU_SSR_CACHE__", 1)[0]
        state = json.loads(re.sub(r'"\s*\+\s*"', "", state_json.rstrip("; \n")))

        for key, location in state.items():
            if not key.startswith("RestaurantLocation:") or location.get("country") != "US":
                continue
            if not location.get("isLocationEnabled") or location.get("isLocationClosed"):
                continue
            if not location.get("openingRanges"):
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
                image=location.get("photoUrl"),
            )

            content = Selector(text=location.get("customLocationContent") or "")
            if website := content.xpath('(//a[contains(@class, "details-button")]/@href)[1]').get():
                item["website"] = response.urljoin(website)

            hours = OpeningHours()
            for opening_range_ref in location["openingRanges"]:
                opening_range = state[opening_range_ref["__ref"]]
                open_time = self.seconds_to_time(opening_range["openTime"])
                close_time = self.seconds_to_time(opening_range["closeTime"])
                for day in opening_range["days"]:
                    hours.add_range(day, open_time, close_time)
            item["opening_hours"] = hours

            apply_category(Categories.FAST_FOOD, item)
            yield item

    @staticmethod
    def seconds_to_time(seconds: int) -> str:
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}"
