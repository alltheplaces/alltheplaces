import csv
from typing import Any, AsyncIterator, ClassVar

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.searchable_points import open_searchable_points


class FirstWatchSpider(Spider):
    name = "first_watch"
    item_attributes: ClassVar = {"brand": "First Watch", "brand_wikidata": "Q5454064", "name": "First Watch"}
    requires_proxy = True  # US-only site, geoblocks non-US IPs

    def make_request(self, lat: str, lon: str, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.firstwatch.com/api/locations.php?latitude={lat}&longitude={lon}&page={page}",
            callback=self.parse,
            cb_kwargs={"lat": lat, "lon": lon, "page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The API only returns the 10 closest locations to a given point, so
        # a grid of search points covering the US is used, paging through
        # each point's results until an empty page is returned.
        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            for point in csv.DictReader(points):
                yield self.make_request(point["latitude"], point["longitude"], 0)

    def parse(self, response: Response, lat: str, lon: str, page: int, **kwargs: Any) -> Any:
        stores = response.json()
        if not stores:
            return

        for location in stores:
            if location.get("status") != "open":
                # e.g. "coming soon" locations that have not yet opened
                continue

            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["ref"] = location["id"]
            item["branch"] = item.pop("name")
            item["street_address"] = location["address"]
            item["country"] = "US"
            item["website"] = f"https://www.firstwatch.com/locations/{location['slug']}"
            apply_category(Categories.RESTAURANT, item)

            yield item

        if len(stores) == 10:
            yield self.make_request(lat, lon, page + 1)
