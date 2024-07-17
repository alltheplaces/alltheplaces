from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class X2oBESpider(Spider):
    name = "x2o_be"
    item_attributes = {"name": "X2O", "brand": "X2O", "brand_wikidata": "Q126165101"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.x2o.be/graphql",
            data={
                "query": """
                    query {
                        storeLocatorStores {
                            address
                            name: store
                            url_key
                            closedExceptions {
                                date
                                description
                                isClosed
                            }
                            location {
                                lat
                                lng
                            }
                            openingHours {
                                openDayIndex
                                openTime
                                closeTime
                            }
                            ref: gmb_store_id
                        }
                    }""",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["storeLocatorStores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("X2O - ").strip()
            item["website"] = item["extras"]["website:nl"] = "https://www.x2o.be/nl/showrooms/{}".format(
                location["url_key"]
            )
            item["extras"]["website:fr"] = "https://www.x2o.be/fr/showrooms/{}".format(location["url_key"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]:
                item["opening_hours"].add_range(DAYS[rule["openDayIndex"] - 1], rule["openTime"], rule["closeTime"])

            apply_category(Categories.SHOP_BATHROOM_FURNISHING, item)

            yield item
