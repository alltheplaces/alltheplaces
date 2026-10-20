from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PagueMenosBRSpider(Spider):
    name = "pague_menos_br"
    item_attributes = {"brand": "Pague Menos", "brand_wikidata": "Q7124466"}

    def make_request(self, latitude: float, longitude: float, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.paguemenos.com.br/api/checkout/pub/pickup-points?geoCoordinates={longitude};{latitude}&pageSize=100&page={page}",
            meta={"latitude": latitude, "longitude": longitude, "page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        for latitude, longitude in country_iseadgg_centroids("BR", 48):
            yield self.make_request(latitude, longitude, 1)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request | Feature]:
        data = response.json()
        for entry in data["items"]:
            location = entry["pickupPoint"]
            if not location.get("isActive") or "Locker" in (location.get("friendlyName") or ""):
                continue
            location.update(location.pop("address"))
            location["longitude"], location["latitude"] = location["geoCoordinates"]
            location["street-number"] = location.get("number")
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            for rule in location.get("businessHours") or []:
                item["opening_hours"].add_range(
                    DAYS[rule["DayOfWeek"] - 1], rule["OpeningTime"], rule["ClosingTime"], time_format="%H:%M:%S"
                )
            apply_category(Categories.PHARMACY, item)
            yield item

        if response.meta["page"] < data["paging"]["pages"]:
            yield self.make_request(response.meta["latitude"], response.meta["longitude"], response.meta["page"] + 1)
