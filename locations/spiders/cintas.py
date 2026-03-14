import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.items import Feature


class CintasSpider(Spider):
    name = "cintas"
    item_attributes = {"brand_wikidata": "Q1092571"}
    allowed_domains = ["cintas.com"]
    start_urls = ["https://www.cintas.com/location-finder/GetLocationsByGeoCoordinates"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            # A few search locations are needed to cover the United States and Canada
            yield JsonRequest(
                url=url, method="POST", data={"lat": "38.80", "lng": "-116.42", "radiusInMiles": 10000}
            )  # Nevada
            yield JsonRequest(
                url=url, method="POST", data={"lat": "35.52", "lng": "-86.58", "radiusInMiles": 10000}
            )  # Tennessee
            yield JsonRequest(
                url=url, method="POST", data={"lat": "46.88", "lng": "-110.36", "radiusInMiles": 10000}
            )  # Montana
            yield JsonRequest(
                url=url, method="POST", data={"lat": "51.25", "lng": "-85.32", "radiusInMiles": 10000}
            )  # Ontario

    def parse(self, response):
        for location in response.xpath("//li[@data-location]"):
            properties = {
                "ref": location.xpath(".//@data-item-id").get(),
                "name": location.xpath('.//h2[@class="locations-results__data-title"]/text()').get().strip(),
                "lat": location.xpath(".//@data-lat").get(),
                "lon": location.xpath(".//@data-lng").get(),
                "addr_full": re.sub(
                    r"\s+",
                    " ",
                    ", ".join(
                        filter(None, location.xpath('.//p[@class="locations-results__data-address"]/text()').getall())
                    ),
                ).strip(),
            }
            if phone := location.xpath('.//div[@class="locations-results__data-tel"]/p[2]/a/@href').get():
                properties["phone"] = phone
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(
                " ".join(
                    filter(None, location.xpath('.//div[@class="locations-results__data-tel"]/p[1]/text()').getall())
                )
            ),
            yield Feature(**properties)
