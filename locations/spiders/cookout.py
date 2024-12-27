import scrapy

from locations.items import Feature


class CookoutSpider(scrapy.Spider):
    name = "cookout"
    item_attributes = {"brand": "Cook Out", "brand_wikidata": "Q5166992"}
    start_urls = [
        "https://cookout.com/wp-admin/admin-ajax.php?action=store_search&lat=40.71278&lng=-74.00597&max_results=500&search_radius=1000"
    ]

    def parse(self, response):
        data = response.json()

        for store in data:
            properties = {
                "ref": store["id"],
                "name": store["store"],
                "website": store["url"],
                "street_address": store.get("address"),
                "city": store.get("city"),
                "state": store.get("state"),
                "postcode": store.get("zip"),
                "country": store.get("country"),
                "lon": float(store["lng"]),
                "lat": float(store["lat"]),
            }

            phone = store["phone"]
            if phone:
                properties["phone"] = phone

            yield Feature(**properties)
