import scrapy

from locations.items import Feature


class RicohEuropeSpider(scrapy.Spider):
    name = "ricoh_europe"
    item_attributes = {"brand": "Ricoh"}
    allowed_domains = ["ricoh-europe.com"]
    REF = 0

    def start_requests(self):
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

            yield scrapy.Request(url=url, callback=self.parse)

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

                yield Feature(**properties)
            else:
                pass
