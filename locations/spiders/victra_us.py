from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class VictraUSSpider(Spider):
    name = "victra_us"
    item_attributes = {
        "brand": "Verizon",
        "brand_wikidata": "Q919641",
        "operator": "Victra",
        "operator_wikidata": "Q118402656",
    }
    allowed_domains = ["victra.com"]

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in country_iseadgg_centroids(["US"], 158):
            yield Request(
                url=f"https://victra.com/wp-json/vcsl/v1/stores?lat={lat}&lng={lon}&radius=100&max=500",
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json().get("stores"):
            item = DictParser.parse(store)

            item["branch"] = (
                item.pop("name", None).replace(item.get("state", ""), "").replace("Verizon Store in ", "").strip(" -,")
            )
            item["addr_full"] = None

            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item
