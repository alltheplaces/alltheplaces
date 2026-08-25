from typing import Any

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class AdidasSpider(PlaywrightSpider):
    name = "adidas"
    item_attributes = {"brand": "Adidas", "brand_wikidata": "Q3895"}
    start_urls = ["https://www.adidas.com/gw/locations/stores/directory"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for countries in DictParser.iter_matching_keys(response.json(), "countries"):
            for country in countries:
                yield JsonRequest(
                    url=f'https://www.adidas.com/gw/locations/stores/directory/{country["country_code"]}',
                    callback=self.parse_stores,
                    cb_kwargs={"country": country["country_code"]},
                )

    def parse_stores(self, response: Response, country: str) -> Any:
        for stores in DictParser.iter_matching_keys(response.json(), "stores"):
            for store in stores:
                store.update(store.pop("location", {}))
                item = DictParser.parse(store)
                item["street_address"] = merge_address_lines(
                    [store["address"].get("address_line1"), store["address"].get("address_line2")]
                )
                item["country"] = country

                if opening_hours := store.get("opening_hours"):
                    item["opening_hours"] = self.parse_opening_hours(opening_hours)

                apply_category(Categories.SHOP_SPORTS, item)

                if store["status"] == "CLOSED":
                    set_closed(item)

                yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            day = rule["day"]
            if rule.get("status") == "CLOSED":
                opening_hours.set_closed(day)
                continue
            opening_hours.add_range(day, rule["hours"]["from"], rule["hours"]["to"])
        return opening_hours
