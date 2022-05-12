# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class TwentyFourHourFitnessSpider(scrapy.Spider):
    name = "24_hour_fitness"
    item_attributes = {"brand": "24 Hour Fitness", "brand_wikidata": "Q4631849"}
    allowed_domains = ["www.24hourfitness.com"]
    start_urls = ("https://www.24hourfitness.com",)
    download_delay = 0.1

    def start_requests(self):
        url = "https://www.24hourfitness.com/Website/ClubLocation/OpenClubs/"

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Host": "www.24hourfitness.com",
            "Referer": "https://www.24hourfitness.com/health_clubs/find-a-gym/",
            "X-Requested-With": "XMLHttpRequest",
        }

        yield scrapy.http.Request(
            url,
            self.parse,
            method="GET",
            headers=headers,
        )

    def parse(self, response):
        result = response.json()

        if "clubs" in result.keys():
            for club in result.get("clubs"):

                ref = club.get("clubNumber")
                name = club.get("name")
                street = club.get("address").get("street")
                city = club.get("address").get("city")
                state = club.get("address").get("state")
                postalcode = club.get("address").get("zip")
                lat = club.get("coordinate").get("latitude")
                lon = club.get("coordinate").get("longitude")
                phone = club.get("phoneNumber")
                website = club.get("linkURL")

                properties = {
                    "ref": ref,
                    "name": name,
                    "street": street,
                    "city": city,
                    "state": state,
                    "postcode": postalcode,
                    "lat": lat,
                    "lon": lon,
                    "phone": phone,
                    "website": website,
                }

                yield GeojsonPointItem(**properties)
