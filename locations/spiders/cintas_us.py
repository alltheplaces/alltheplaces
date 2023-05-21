import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.items import Feature


class CintasUSSpider(Spider):
    name = "cintas_us"
    item_attributes = {"brand": "Cintas", "brand_wikidata": "Q1092571"}
    allowed_domains = ["cintas.com"]
    start_urls = ["https://www.cintas.com/location-finder/GetLocationsByGeoCoordinates"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data={"lat": "44.97", "lng": "-103.77", "radiusInMiles": 100000})

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
