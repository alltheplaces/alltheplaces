from typing import Iterable

import xmltodict
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class TheEntertainerGBSpider(PlaywrightSpider):
    name = "the_entertainer_gb"
    item_attributes = {"brand": "The Entertainer", "brand_wikidata": "Q7732289"}
    start_urls = [
        "https://www.thetoyshop.com/api/occ/v2/thetoyshop/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=1200&query=doncaster&storeType=ALL&radius=10000000&sort=asc"
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in xmltodict.parse(response.body)["storeFinderSearchPage"].get("stores", []):
            item = DictParser.parse(feature)
            item["ref"] = feature["address"]["id"]
            item["website"] = "https://www.thetoyshop.com/store/" + feature["name"].lower().replace(" ", "-")
            item["street_address"] = merge_address_lines(
                [feature["address"].get("line1"), feature["address"].get("line2")]
            )
            item["phone"] = feature["address"].get("phone")
            item["branch"] = item.pop("name")
            item["opening_hours"] = self.parse_opening_hours(feature.get("openingHours", {}))
            if "tesco" in item["website"]:
                continue
                # item["located_in"] = "Tesco"
                # item["located_in_wikidata"] = "Q487494"

            apply_category(Categories.SHOP_TOYS, item)
            yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours.get("weekDayOpeningList", []):
            if rule.get("closed") != "false":
                oh.set_closed(rule["weekDay"])
            else:
                oh.add_range(
                    rule["weekDay"],
                    rule["openingTime"]["formattedHour"],
                    rule["closingTime"]["formattedHour"],
                )
        return oh
