from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class RulerFoodsUSSpider(Spider):
    name = "ruler_foods_us"
    item_attributes = {"brand": "Ruler Foods", "brand_wikidata": "Q17125470"}
    allowed_domains = ["falcon.shop.inmar.io"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://falcon.shop.inmar.io/v2/session",
            method="POST",
            headers={"Inmar-Banner-Id": "ruler_foods"},
            callback=self.parse_session,
        )

    def parse_session(self, response: Response) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://falcon.shop.inmar.io/v2/locations?fulfillmentMethod=instore",
            headers={"Inmar-Session-Id": response.json()["data"]["item"]["sessionId"]},
        )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for location in response.json()["data"]["item"]["modules"]["itemListModules"][0]["items"]["locationItems"]:
            location.update(location.pop("locationAddress"))
            item = DictParser.parse(location)
            item["branch"] = (item.pop("name", None) or "").removeprefix("Ruler Foods ").strip(" -")
            item["phone"] = location.get("locationPhone")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
