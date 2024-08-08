import json
import re

import scrapy

from locations.items import Feature


class EuromobilNLSpider(scrapy.Spider):
    name = "euromobil_nl"
    start_urls = ["https://euromobil.nl/contact/"]

    item_attributes = {"brand": "Euromobil", "brand_wikidata": "Q1375118"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+partners\s*=\s*(\[.*?\]);\s*var"
        raw = response.xpath("//script[contains(., 'var stores =')]/text()")
        stores_json = json.loads(re.search(pattern, raw.extract_first(), re.DOTALL).group(1))
        for store in stores_json:
            coordinates = store.get("geo")
            yield Feature(
                {
                    "ref": store.get("nummer"),
                    "name": store.get("title"),
                    "street_address": store.get("adres"),
                    "addr_full": coordinates.get("address"),
                    "phone": store.get("phone"),
                    "email": store.get("email"),
                    "postcode": store.get("zip"),
                    "city": store.get("plaats"),
                    "website": store.get("website"),
                    "lat": coordinates.get("lat"),
                    "lon": coordinates.get("lng"),
                }
            )
