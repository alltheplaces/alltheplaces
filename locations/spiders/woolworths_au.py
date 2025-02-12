from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class WoolworthsAUSpider(scrapy.Spider):
    name = "woolworths_au"
    METRO = {"brand": "Woolworths Metro", "brand_wikidata": "Q111772555"}
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q3249145"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=10000&Division=SUPERMARKETS&Facility=&postcode=*"
    ]
    user_agent = BROWSER_DEFAULT
    requires_proxy = "AU"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["AddressLine1"], location["AddressLine2"]])
            item["ref"] = location["StoreNo"]
            item["city"] = location["Suburb"]

            item["website"] = "https://www.woolworths.com.au/shop/storelocator/" + "-".join(
                [item["state"], item["city"], item["ref"]]
            ).lower().replace(" ", "-")

            if "Metro" in item["branch"]:
                item["branch"] = item["branch"].replace("Metro", "").strip(" ()")
                item.update(self.METRO)

            apply_yes_no(Extras.WIFI, item, "WiFi" in location["Facilities"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
