from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VubSKSpider(Spider):
    name = "vub_sk"
    item_attributes = {"brand": "VÚB banka", "brand_wikidata": "Q12778981"}

    async def start(self) -> AsyncIterator[Any]:
        for location_type in ("BRANCH", "ATM"):
            yield JsonRequest(
                url="https://www.vub.sk/digitalServicesServlet/?operation=searchLocations&headers=lbsHeader&endpointName=searchLocations&locale=en&bank=VUB",
                data={"search": {"locationType": location_type, "size": 1000, "start": 0}},
                headers={
                    "Origin": "https://www.vub.sk",
                    "Referer": "https://www.vub.sk/ludia/pobocky-bankomaty.html",
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json().get("availableLocations", []):
            item = DictParser.parse(poi)

            if poi.get("type") == "BRANCH":
                item["branch"] = item.pop("name", None)
                apply_category(Categories.BANK, item)
            elif poi.get("type") == "ATM":
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected VÚB location type: %s", poi.get("type"))
                continue

            yield item
