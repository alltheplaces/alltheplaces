from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SteakNShakeSpider(scrapy.Spider):
    name = "steak_n_shake"
    item_attributes = {"brand_wikidata": "Q7605233"}
    allowed_domains = ["www.steaknshake.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.steaknshake.com/wp-admin/admin-ajax.php?action=get_location_data_from_plugin"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_data in response.json():
            properties = {
                "ref": store_data["brandChainId"],
                "street_address": store_data["address"]["address1"],
                "city": store_data["address"]["city"],
                "state": store_data["address"]["region"],
                "postcode": store_data["address"]["zip"],
                "country": store_data["address"]["country"],
                "phone": store_data["phone1"],
                "lat": store_data["address"]["loc"][1],
                "lon": store_data["address"]["loc"][0],
                "website": f"https://www.steaknshake.com/locations/{store_data['slug']}/",
            }

            apply_category(Categories.FAST_FOOD, properties)

            yield Feature(**properties)

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
        # "sets" and "hours" do not match, website uses "hours" but quality doesn't seem great
        oh = OpeningHours()
        for rules in hours["sets"]:
            if rules["name"] != "Hours of Operation":
                continue
            for day, times in rules["days"].items():
                for time in times:
                    oh.add_range(day, str(time["start"]).zfill(4), str(time["end"]).zfill(4), "%H%M")

        return oh
