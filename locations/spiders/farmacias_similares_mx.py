from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class FarmaciasSimilaresMXSpider(Spider):
    name = "farmacias_similares_mx"
    item_attributes = {"brand_wikidata": "Q62564610"}

    def make_request(self, latitude: float, longitude: float, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.farmaciasdesimilares.com/api/checkout/pub/pickup-points?geoCoordinates={longitude};{latitude}&pageSize=100&page={page}",
            meta={"latitude": latitude, "longitude": longitude, "page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        for latitude, longitude in country_iseadgg_centroids("MX", 48):
            yield self.make_request(latitude, longitude, 1)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request | Feature]:
        data = response.json()
        for entry in data["items"]:
            location = entry["pickupPoint"]
            location["name"] = location.pop("friendlyName")
            location.update(location.pop("address"))
            location["longitude"], location["latitude"] = location.pop("geoCoordinates")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["housenumber"] = location["number"]
            item["opening_hours"] = OpeningHours()
            for rule in location.get("businessHours") or []:
                item["opening_hours"].add_range(
                    DAYS[rule["DayOfWeek"] - 1], rule["OpeningTime"], rule["ClosingTime"], time_format="%H:%M:%S"
                )
            apply_category(Categories.PHARMACY, item)
            yield item

        if response.meta["page"] < data["paging"]["pages"]:
            yield self.make_request(response.meta["latitude"], response.meta["longitude"], response.meta["page"] + 1)
