from scrapy import Spider

from locations.items import Feature


class RossmannPLSpider(Spider):
    name = "rossmann_pl"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    start_urls = ["https://www.rossmann.pl/shops/api/Shops"]

    def parse(self, response):
        data = response.json()["data"]
        for shop in data:
            properties = {
                "ref": shop["shopNumber"],
                "street_address": shop["address"]["street"],
                "city": shop["address"]["city"],
                "postcode": shop["address"]["postCode"],
                "country": "PL",
                "lat": shop["shopLocation"]["latitude"],
                "lon": shop["shopLocation"]["longitude"],
                "website": "https://www.rossmann.pl/drogerie" + shop["navigateUrlV2"],
            }
            yield Feature(**properties)
