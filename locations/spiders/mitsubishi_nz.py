from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no, Extras
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiNZSpider(scrapy.Spider):
    name = "mitsubishi_nz"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://www.mmnz.co.nz/graphql",
            data={
                "query": """
                query Dealers {
                    getDealers {
                        id
                        name
                        addressLine1
                        addressLine2
                        addressLine3
                        primaryPhone
                        primaryEmail
                        website
                        location
                        locationX
                        locationY
                        services
                        leadTime
                    }
                }
            """,
                "variables": {},
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["getDealers"]:
            item = DictParser.parse(location)
            item["lat"] = location["locationY"]
            item["lon"] = location["locationX"]
            item["email"] = location.get("primaryEmail")
            item["state"] = location["location"]
            item["addr_full"] = merge_address_lines(
                [location.pop("addressLine1"), location.pop("addressLine2"), location.pop("addressLine3")]
            )
            if location["services"] in ["new,used,parts,service,finance", "new, parts, service, finance"]:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, True)
                apply_yes_no(Extras.USED_CAR_SALES, item, True if "used" in location["services"] else False)
            elif "parts,service" in location["services"]:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
