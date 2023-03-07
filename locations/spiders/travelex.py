import scrapy

from locations.dict_parser import DictParser
from locations.items import Feature


class TravelexSpider(scrapy.Spider):
    name = "travelex"
    item_attributes = {"brand": "Travelex", "brand_wikidata": "Q2337964"}
    allowed_domains = ["https://www.travelex.co.uk/"]

    def start_requests(self):
        countries = ["dech", "au", "gb", "enbh", "de", "zhhk", "jajp", "my", "nz", "qa", "om", "ae", "nl"]
        for country in countries:
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
                item["street_address"] = row.get("address").get("address1")
                item["city"] = row.get("address").get("city")
                item["postcode"] = row.get("address").get("postalCode")
                item["extras"] = {
                    "directions": row.get("directions"),
                    "notes": row.get("notes"),
                    "terminal": row.get("terminal"),
                }
                if response.meta.get("country") == "nl":
                    item["brand"] = "GWK Travelex"
                yield item
