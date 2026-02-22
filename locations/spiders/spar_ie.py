from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES


class SparIESpider(Spider):
    name = "spar_ie"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    start_urls = ["https://www.spar.ie/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.xpath("//script[contains(text(), 'stores =')]/text()").get()):
            if location["storeStatus"] is False:
                continue

            item = Feature()
            item["ref"] = location["storeId"]
            item["lat"] = location["storeDetails"]["Latitude"]
            item["lon"] = location["storeDetails"]["Longitude"]
            item["street_address"] = merge_address_lines(
                [
                    location["storeDetails"].get("AddressLine1"),
                    location["storeDetails"].get("AddressLine2"),
                    location["storeDetails"].get("AddressLine3"),
                ]
            )
            item["postcode"] = location["storeDetails"]["PostCode"]
            item["phone"] = location["storePhone"]

            apply_yes_no(Extras.ATM, item, "ATM" in location["storeServices"])
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in location["storeServices"])
            apply_yes_no("sells:lottery", item, "Lotto" in location["storeServices"])

            item["branch"] = location["storeName"].removeprefix("SPAR").removeprefix("Spar").strip()
            if item["branch"].startswith("Express"):
                item["branch"] = item["branch"].removeprefix("Express")
                item["name"] = "Spar Express"
            else:
                item["name"] = "Spar"

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
