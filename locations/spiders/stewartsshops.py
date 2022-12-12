import scrapy

from locations.items import GeojsonPointItem


class StewartsShopsSpider(scrapy.Spider):
    name = "stewartsshops"
    item_attributes = {"brand_wikidata": "Q7615690"}
    allowed_domains = ["api.momentfeed.com"]

    def get_page(self, n):
        return scrapy.Request(
            f"https://api.momentfeed.com/v1/analytics/api/llp.json?pageSize=100&page={n}",
            headers={"authorization": "ZGRQTRLWHXDMDNUO"},
            meta={"page": n},
        )

    def start_requests(self):
        yield self.get_page(1)

    def parse(self, response):
        data = response.json()
        if "message" in data:
            return
        yield self.get_page(1 + response.meta["page"])

        for row in data:
            info = row["store_info"]
            fields = {entry["name"]: entry["data"] for entry in row["custom_fields"]}

            properties = {
                "ref": info["corporate_id"],
                "lat": info["latitude"],
                "lon": info["longitude"],
                "name": fields.get("Name") or info["name"],
                "brand": info["brand_name"],
                "street_address": info["address"],
                "city": info["locality"],
                "state": info["region"],
                "postcode": info["postcode"],
                "country": info["country"],
                "phone": info["phone"],
                "website": "https://locations.stewartsshops.com" + row["llp_url"],
                "extras": {
                    "amenity:fuel": "Gas Station" in fields or None,
                    "fuel:diesel": "Diesel" in fields or None,
                    "fuel:e0_octane_91": "Gas Station with 91 Premium Non-Ethanol" in fields or None,
                    "fuel:kerosene": "Kerosene" in fields or None,
                    "atm": "ATM" in fields or None,
                    "car_wash": "Car Wash" in fields or None,
                },
            }
            yield GeojsonPointItem(**properties)
