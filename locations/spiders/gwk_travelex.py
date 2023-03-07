import scrapy

from locations.dict_parser import DictParser
from locations.items import Feature


class TravelexSpider(scrapy.Spider):
    name = "travelex_nl"
    item_attributes = {"brand": "GWK Travelex", "brand_wikidata": "Q2337964"}
    allowed_domains = ["https://www.travelex.co.uk/"]

    def start_requests(self):
        countries = ["nl"]
        for country in countries:
            yield scrapy.Request(
                f"https://api.travelex.net/salt/store/search?key=Travelex&mode=storeLocator&site=/{country}&lat={0.0}&lng={0.0}",
            )

    def parse(self, response):
        data = response.json()
        item_categories = data.get("items")
        for category in item_categories:
            stores = category.get("stores")
            for row in stores:
                item = DictParser.parse(row)
                properties = {
                    "brand": self.item_attributes.get("brand"),
                    "addr_full": row.get("formattedAddress"),
                    "street_address": row.get("address").get("address1"),
                    "city": row.get("address").get("city"),
                    "postcode": row.get("address").get("postalCode"),
                    "extras": {
                        "directions": row.get("directions"),
                        "notes": row.get("notes"),
                        "terminal": row.get("terminal"),
                    },
                }
                item = {**item, **properties}
                yield item
