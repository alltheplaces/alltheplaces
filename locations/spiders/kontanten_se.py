import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class KontantenSESpider(scrapy.Spider):
    name = "kontanten_se"

    item_attributes = {"brand": "Kontanten", "brand_wikidata": "Q122831839", "country": "GB"}

    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://kontanten.se/wp-admin/admin-ajax.php",
            callback=self.parse,
            formdata={
                "action": "markers_data",
                "call": "markers",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            coordinates = store.get("geometry").get("coordinates")
            item = Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("place"),
                    "street_address": store.get("address"),
                    "postcode": store.get("postal"),
                    "city": store.get("city"),
                    "lat": coordinates[0],
                    "lon": coordinates[1],
                }
            )
            apply_category(Categories.ATM, item)
            yield item
