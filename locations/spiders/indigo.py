from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class IndigoSpider(Spider):
    name = "indigo"
    item_attributes = {"operator": "Indigo", "operator_wikidata": "Q3559970"}

    def _make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://salesforce.parkindigo.com/locations?" + urlencode({"location.language": "en", "page": page})
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self._make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for lot in data["content"]:
            item = DictParser.parse(lot)
            item["extras"]["capacity"] = str(lot.get("totalSpaces", None) or "")
            geo = lot.get("geoLocation") or {}
            item["lat"] = geo.get("x")
            item["lon"] = geo.get("y")
            item["street_address"] = ((lot.get("address") or {}).get("lines") or [None])[0]

            apply_category(Categories.PARKING, item)

            yield item

        if not data.get("last"):
            yield self._make_request(data["number"] + 1)
