import scrapy

from locations.dict_parser import DictParser


class TravelexSpider(scrapy.Spider):
    name = "travelex"
    item_attributes = {"brand": "Travelex", "brand_wikidata": "Q2337964"}
    countries = [
        "ae",
        "au",
        "nlbe",
        "enbh",
        "enca",
        "ench",
        "encn",
        "cz",
        "de",
        "fr",
        "gb",
        "enhk",
        "in",
        "itit",
        "enjp",
        "mo",
        "my",
        "nl",
        "nm",
        "nz",
        "om",
        "qa",
        "uk",
        "us",
        "za",
    ]

    # API documentation
    # https://api.travelex.net/docs/api/index.html#api-store-getStoreAll
    #
    # Countries check
    # If a new country is added to the brand, you might want to check them here:
    # https://api.travelex.net/salt/site/list?key=Travelex

    def start_requests(self):
        for country in self.countries:
            yield scrapy.Request(
                f"https://api.travelex.net/salt/store/search?key=Travelex&mode=storeLocator&site=/{country}&lat={0.0}&lng={0.0}",
                meta={"country": country},
            )

    def parse(self, response):
        data = response.json()
        item_categories = data.get("items")
        for category in item_categories:
            stores = category.get("stores")
            for row in stores:
                item = DictParser.parse(row)
                item["addr_full"] = row.get("formattedAddress")
                item["extras"] = {
                    "directions": row.get("directions"),
                    "notes": row.get("notes"),
                    "terminal": row.get("terminal"),
                }
                if response.meta.get("country") == "nl":
                    item["brand"] = "GWK Travelex"
                yield item
