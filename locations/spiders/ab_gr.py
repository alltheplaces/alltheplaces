import json
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class AbGRSpider(Spider):
    name = "ab_gr"
    item_attributes = {"brand": "AB", "brand_wikidata": "Q4721807", "nsi_id": "N/A"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.ab.gr/api/v1/?{}".format(
                urlencode(
                    {
                        "operationName": "GetStoreSearch",
                        "variables": json.dumps(
                            {
                                "pageSize": 3000,
                                "lang": "en",
                                "query": "",
                                "currentPage": 0,
                                "options": "STORELOCATOR_MINIFIED",
                            }
                        ),
                        "extensions": json.dumps(
                            {
                                "persistedQuery": {
                                    "version": 1,
                                    "sha256Hash": "9dc67fed7b358c14d80bbd04c6524ef76f4298a142ed7ab86732442271f4ad46",
                                }
                            }
                        ),
                    }
                )
            )
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["storeSearchJSON"]["stores"]:
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["localizedName"]
            item["addr_full"] = location["address"]["formattedAddress"]
            item["phone"] = "; ".join(location["address"]["phone"].split(","))
            item["website"] = "https://www.ab.gr/storedetails/{}".format(location["urlName"])

            services = [s["code"] for s in location["storeServices"]]
            apply_yes_no(Extras.WIFI, item, "FREEWIFI" in services)

            if location["groceryStoreType"] == "ABCITY":
                item["name"] = "AB City"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)
                if location["groceryStoreType"] == "AB":
                    item["name"] = "ΑΒ Βασιλόπουλος"
                elif location["groceryStoreType"] == "FOODMRKT":
                    item["name"] = "AB Food Market"
                elif location["groceryStoreType"] == "SHOPNGO":
                    item["name"] = "AB Shop & Go"

            yield item
