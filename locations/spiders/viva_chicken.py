import base64
import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class VivaChickenSpider(scrapy.Spider):
    name = "viva_chicken"
    item_attributes = {"brand": "Viva Chicken"}
    allowed_domains = ["www.vivachicken.com"]
    start_urls = ["https://www.vivachicken.com/locations"]

    def parse(self, response):
        data = json.loads(base64.b64decode(response.xpath("//@data-editor").get()))
        for row in data["locations"]:
            properties = {
                "addr_full": row["displayAddress"],
                "ref": row["uniqueId"],
                "name": row["title"],
                "lat": row["latitude"],
                "lon": row["longitude"],
            }
            item = Feature(**properties)
            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "chicken"
            yield item
