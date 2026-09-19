from typing import Any, Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

# Rally House is not present in NSI (checked against brand_wikidata Q121086620),
# so "brand" is omitted here rather than guessing a string.


class RallyHouseUSSpider(CamoufoxSpider):
    name = "rally_house_us"
    item_attributes = {"brand_wikidata": "Q121086620"}
    start_urls = ["https://www.rallyhouse.com/feeds/store-locator/store-locator.json"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//pre[contains(text(), "FeatureCollection")]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for feature in response.json()["features"]:
            properties = feature["properties"]

            # A handful of "coming soon" locations are flagged forcedClosed
            # with a placeholder photo and no confirmed opening yet.
            if properties.get("forcedClosed"):
                continue

            item = Feature()
            item["ref"] = properties["id"]
            item["name"] = properties["name"]
            item["lon"], item["lat"] = feature["geometry"]["coordinates"]
            item["street_address"] = properties["address"]
            item["city"] = properties["city"]
            item["state"] = properties["state"]
            item["postcode"] = properties["zip"].zfill(5)
            item["country"] = "US"
            item["phone"] = properties.get("phone")
            item["website"] = "https://www.rallyhouse.com" + properties["url"]
            item["image"] = properties.get("photo")

            oh = OpeningHours()
            for day_key, day in zip(DAYS_3_LETTERS, DAYS):
                if hours_range := (properties.get("hours") or {}).get(day_key.lower()):
                    open_time, close_time = hours_range.split(" - ")
                    oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_SPORTS, item)

            yield item
