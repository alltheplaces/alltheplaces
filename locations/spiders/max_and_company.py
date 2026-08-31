import html
import re

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MaxAndCompanySpider(PlaywrightSpider):
    name = "max_and_company"
    item_attributes = {"brand": "MAX&Co.", "brand_wikidata": "Q120570926"}
    start_urls = [
        "https://gb.maxandco.com/store-locator?south=-90&west=-180&north=90&east=180&listJson=true&withoutRadius=false"
    ]
    no_refs = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        for location in response.json()["features"]:
            item = DictParser.parse(location["properties"])
            item.pop("name", None)
            branch = html.unescape(location["properties"]["displayName"])
            item["branch"] = re.sub(r"^max\s*&\s*co\.?\s*", "", branch, flags=re.IGNORECASE) or None
            item["addr_full"] = location["properties"]["formattedAddress"]
            item["state"] = location["properties"]["prov"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["properties"]["openingHours"].items():
                if day := sanitise_day(day):
                    for time in times:
                        start_time, end_time = time.split(" - ")
                        if end_time == "24.00":
                            end_time = "23.59"
                        item["opening_hours"].add_range(day, start_time, end_time, time_format="%I.%M %p")

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
