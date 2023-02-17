import json

import scrapy

from locations.hours import DAYS_SE, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class Dats24BESpider(scrapy.Spider):
    name = "dats24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576"}
    start_urls = ["https://customer.dats24.be/wps/portal/datscustomer/fr/b2c/locator"]

    def parse(self, response, **kwargs):
        script_tags = response.text.split("<script")
        for script_tag in script_tags:
            if 'class="locatorMapData"' in script_tag:
                # Extract the JSON data from the <script> tag
                start_index = script_tag.find('>') + 1
                end_index = script_tag.find('</script>', start_index)
                json_data = script_tag[start_index:end_index]
                break
        # Load the JSON data as a Python object using the json library
        data = json.loads(json_data)

        for store in data.get("store"):
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "street_address": store.get("address"),
                    "postcode": store["postalCode"],
                    "city": store["city"],
                    "phone": store.get("phone"),
                    "website": f"https://www.coop.se{store.get('url')}" if store.get("url") else None,
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "opening_hours": oh,
                    "extras": {"store_type": store.get("concept").get("name")},
                }
            )
