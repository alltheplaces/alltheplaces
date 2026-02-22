import json
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class DollarCurtainsAndBlindsAUSpider(PlaywrightSpider):
    name = "dollar_curtains_and_blinds_au"
    item_attributes = {"brand": "dollar curtains+blinds", "brand_wikidata": "Q122430680"}
    allowed_domains = ["www.dollarcurtainsandblinds.com.au"]
    start_urls = ["https://www.dollarcurtainsandblinds.com.au/app/themes/dcb-tailwind-2/cache/store-cache.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//pre/text()").get("")):
            location.update(location.pop("map_location"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("dollar curtains + blinds ")
            item["name"] = self.item_attributes["brand"]
            item["ref"] = item["website"] = location["link"]
            item["addr_full"] = location["address_formatted"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["open_hours"])
            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
