import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MitsubishiPLSpider(Spider):
    name = "mitsubishi_pl"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi.pl/dealerzy"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"dealerLocations\":(\[.*\])}\]\],\[\[\"\$\"",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["addr_full"] = location["full_address"]
            item["name"] = location["dealer_name"]

            services = location["services"]
            if "SHOWROOM" in services:
                apply_category(Categories.SHOP_CAR, item)
                if "SERVICE" in services:
                    apply_yes_no(Extras.CAR_REPAIR, item, True)
            elif "SERVICE" in services:
                apply_category(Categories.SHOP_CAR_REPAIR, item)

            if isinstance(location["dealer_websites"], list):
                item["website"] = location["dealer_websites"][0]["url"]

            yield item
