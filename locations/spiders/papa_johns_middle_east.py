from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.dict_parser import DictParser


class PapaJohnsMiddleEastSpider(Spider):
    name = "papa_johns_middle_east"
    item_attributes = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}

    def start_requests(self) -> Iterable[Request]:
        for country, slug in [("ae", ""), ("qa", "qatar"), ("sa", "ksa")]:
            website = f"https://order.papajohns.{country}/papajohns{slug}/store-locator/?lang=en"
            yield JsonRequest(
                url=f"https://order.papajohns.{country}/api/outlet/list/?all=true",
                headers={"Referer": website},
                meta=dict(country=country, website=website),
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("list", []):
            if store["public"] is False:
                continue
            item = DictParser.parse(store)
            item["name"] = None
            item["addr_full"] = store.get("address", {}).get("en")
            item["extras"]["addr:full:ar"] = store.get("address", {}).get("ar")
            item["branch"] = store.get("name", {}).get("en")
            item["extras"]["branch:ar"] = store.get("name", {}).get("ar")
            item["phone"] = store.get("phone", [{}])[0].get("value")
            item["lat"], item["lon"] = store["points"]
            item["country"] = response.meta["country"]
            item["website"] = response.meta["website"]
            yield item
