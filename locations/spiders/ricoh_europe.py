from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.items import Feature


class RicohEuropeSpider(Spider):
    name = "ricoh_europe"
    item_attributes = {"brand": "Ricoh"}
    allowed_domains = ["ricoh-europe.com"]
    REF = 0

    async def start(self) -> AsyncIterator[Request]:
        countries = [
            "United Kingdom",
            "France",
            "Germany",
            "Netherlands",
            "Austria",
            "Belgium",
            "Czech Republic",
            "Denmark",
            "Luxembourg",
            "Norway",
            "Poland",
            "Portugal",
            "Russia",
            "Slovakia",
            "South Africa",
            "Spain",
            "Sweden",
            "Switzerland",
            "Turkey",
            "Finland",
            "Hungary",
            "Ireland",
            "Italy",
        ]

        base_url = "https://www.ricoh-europe.com/api/dealerfinder/product/country/{country}/"

        for country in countries:
            url = base_url.format(country=country)

            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        stores = response.json()

        for store in stores["Dealers"]:
            self.REF += 1
            if "ricoh" in store["Url"]:
                properties = {
                    "ref": self.REF,
                    "name": store["Name"],
                    "street_address": store["Address"]["Street"],
                    "city": store["Address"]["City"],
                    "state": store["Address"]["Area"],
                    "postcode": store["Address"]["Zip"],
                    "country": store["Address"]["Country"],
                    "lat": store["Latitude"],
                    "lon": store["Longitude"],
                    "phone": store["Phone"],
                }
                apply_category(Categories.OFFICE_COMPANY, properties)
                apply_category({"company": "consulting"}, properties)
                yield Feature(**properties)
            else:
                pass
