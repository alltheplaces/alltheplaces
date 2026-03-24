from typing import AsyncIterator

from scrapy.http import Request

from locations.geo import point_locations
from locations.spiders.swarovski_us import SwarovskiUSSpider


class SwarovskiEUSpider(SwarovskiUSSpider):
    name = "swarovski_eu"
    item_attributes = {"brand": "Swarovski", "brand_wikidata": "Q611115"}
    allowed_domains = ["swarovski.com"]

    async def start(self) -> AsyncIterator[Request]:
        point_files = "eu_centroids_120km_radius_country.csv"
        for lat, lon in point_locations(point_files):
            yield Request(
                url=f"https://www.swarovski.com/en-LU/store-finder/stores/?geoPoint.latitude={lat}&geoPoint.longitude={lon}&provider=GOOGLE&allBaseStores=true&radius=120&clientTimeZoneOffset=-60",
            )
