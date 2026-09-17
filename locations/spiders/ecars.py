import logging
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import make_subdivisions


class EcarsSpider(Spider):
    name = "ecars"
    item_attributes = {"brand": "ESB ecars", "brand_wikidata": "Q134882112"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, bounds: tuple[float, float, float, float]) -> JsonRequest:
        xmin, ymin, xmax, ymax = bounds
        return JsonRequest(
            url="https://myaccount.esbecars.com/stationFacade/findSitesInBounds",
            data={
                "filterByBounds": {
                    "northEastLat": ymax,
                    "northEastLng": xmax,
                    "southWestLat": ymin,
                    "southWestLng": xmin,
                }
            },
            cb_kwargs={"bounds": bounds},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request((-180, -90, 180, 90))

    def parse(self, response, bounds, **kwargs):
        result = response.json()
        if not result["success"]:
            self.log(result["errors"], logging.ERROR)
            return

        for location in result["data"]:
            if location["deleted"]:
                continue

            if location.get("cluster"):
                # The API groups sites into map clusters and omits per-site
                # details (e.g. "dn") once too many sites fall within the
                # queried bounds. Split the bounds into smaller tiles and
                # re-query each one until individual site data is returned.
                for subdivision in make_subdivisions(bounds, 2):
                    yield self.make_request(subdivision)
                return

            item = DictParser.parse(location)
            item["addr_full"] = location["dn"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
