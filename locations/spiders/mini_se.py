import scrapy

from locations.categories import Categories
from locations.items import Feature


# TODO: Is this fully covered by the BMW Group Spider?
class MiniSESpider(scrapy.Spider):
    name = "mini_se"
    item_attributes = {"brand": "Mini", "brand_wikidata": "Q116232", "extras": Categories.SHOP_CAR.value}
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
