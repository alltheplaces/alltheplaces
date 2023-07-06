import json
import re

import scrapy

from locations.items import Feature


class BigmatBESpider(scrapy.Spider):
    name = "bigmat_be"
    start_urls = ["https://www.bigmat.be/magasins"]

    item_attributes = {"brand": "BigMat", "brand_wikidata": "Q101851862"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+stores\s*=\s*(\[.*?\]);\s*var"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            yield Feature(
                {
                    "ref": store.get("id_store"),
                    "name": store.get("name"),
                    "street_address": store.get("address1"),
                    "phone": store.get("phone"),
                    "email": store.get("email"),
                    "postcode": store.get("postcode"),
                    "city": store.get("city"),
                    "website": store.get("link"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                }
            )
