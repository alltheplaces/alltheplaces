import json
from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.google_url import url_to_coords


class AuchanHUSpider(Spider):
    name = "auchan_hu"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(url="https://auchan.hu/api/v2/cache/petrol/list", callback=self.parse_petrol)
        yield Request(url="https://auchan.hu/aruhazak", callback=self.parse_stores)

    def parse_petrol(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"], item["lon"] = url_to_coords(location["googleMapsLink"])
            item["branch"] = item.pop("name").removeprefix("MH Auchan ").removesuffix(" benzinkút")
            item["name"] = "Auchan"
            item["website"] = urljoin("https://auchan.hu/petrol/", location["slug"])
            apply_category(Categories.FUEL_STATION, item)
            item["nsi_id"] = "N/A"
            yield item

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        nuxt_data = response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()
        payload = json.loads(nuxt_data)

        def resolve(idx: int, seen: frozenset = frozenset()) -> Any:
            if not isinstance(idx, int) or idx < 0 or idx >= len(payload) or idx in seen:
                return None
            seen = seen | {idx}
            node = payload[idx]
            if isinstance(node, list):
                if len(node) == 2 and node[0] in ("ShallowReactive", "Reactive", "Ref"):
                    return resolve(node[1], seen)
                return [resolve(x, seen) if isinstance(x, int) else x for x in node]
            if isinstance(node, dict):
                return {k: resolve(v, seen) if isinstance(v, int) else v for k, v in node.items()}
            return node

        pinia = resolve(payload[1]["pinia"])
        for location in pinia["storesAndPetrolsStore"]["stores"]:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = url_to_coords(location["googleMapsLink"])
            item["branch"] = item.pop("name").removeprefix("Auchan ")
            item["website"] = urljoin("https://auchan.hu/stores/", location["slug"])
            item.pop("phone", None)
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
