import scrapy
import xmltodict

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MiniSESpider(scrapy.Spider):
    name = "mini_se"
    item_attributes = {
        "brand": "Mini",
        "brand_wikidata": "Q116232",
    }
    start_urls = ["https://www.mini.se/umbraco/api/dealers/getall?nodeId=1870"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def parse(self, response):
        stores = response.json()
        for store in stores:
            if not store.get("IsReseller"):
                continue
            yield Feature(
                {
                    "ref": store["BuNo"],
                    "name": store["DealerName"],
                    "street_address": store["Address"],
                    "postcode": store["PostalCode"],
                    "city": store["City"],
                    "phone": store["Tel"],
                    "lat": store["Coords1"],
                    "lon": store["Coords2"],
                    "email": store["EmailSales"],
                    "website": store["SiteLink"],
                }
            )
