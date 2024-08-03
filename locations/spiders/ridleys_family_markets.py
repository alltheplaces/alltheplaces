import scrapy

from locations.categories import Categories
from locations.items import Feature


class RidleysFamilyMarketsSpider(scrapy.Spider):
    name = "ridleys_family_markets"
    item_attributes = {
        "brand": "Ridley's Family Markets",
        "brand_wikidata": "Q7332999",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://shopridleys.com/_ajax_map.php"]

    def parse(self, response):
        results = response.json()
        for data in results:
            props = {
                "ref": data.get("storeNumber"),
                "street_address": data.get("streetAddress"),
                "name": data.get("storeName"),
                "city": data.get("city"),
                "postcode": data.get("zip"),
                "state": data.get("state"),
                "website": data.get("rio_url"),
                "phone": data.get("phone"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "country": "US",
            }

            yield Feature(**props)
