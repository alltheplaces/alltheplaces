import scrapy

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
                properties = {
                    "ref": row.get("storeId"),
                    "name": row.get("name"),
                    "addr_full": row.get("formattedAddress"),
                    "brand": self.item_attributes.get("brand"),
                    "street_address": row.get("address").get("address1"),
                    "city": row.get("address").get("city"),
                    "postcode": row.get("address").get("postalCode"),
                    "lat": float(row.get("lat")),
                    "lon": float(row.get("lng")),
                    "website": row.get("storeUrl"),
                    "extras": {
                        "directions": row.get("directions"),
                        "notes": row.get("notes"),
                        "terminal": row.get("terminal")
                    }
                }
                yield Feature(**properties)
