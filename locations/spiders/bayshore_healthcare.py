import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BayshoreHealthcareSpider(scrapy.Spider):
    name = "bayshore_healthcare"
    item_attributes = {"brand": "Bayshore Healthcare"}
    allowed_domains = ["bayshore.ca"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.bayshore.ca/wp-admin/admin-ajax.php?action=location_finder&language=en"

        headers = {
            "origin": "https://www.bayshore.ca",
            "Referer": "https://www.bayshore.ca/locations/",
        }

        formdata = {
            "search_type": "location",
        }

        yield scrapy.http.FormRequest(url, self.parse, method="POST", headers=headers, formdata=formdata)

    def parse(self, response):
        stores = json.loads(response.body)

        for store in stores["result"]["entries"]:
            if addr_full := store.get("address"):
                addr_full = clean_address(addr_full)
            coords = store["latlng"].split(",")
            lat = coords[0]
            lng = coords[1]

            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": addr_full,
                "country": "CA",
                "lat": lat,
                "lon": lng,
                "phone": store["local_telephone"],
                "website": "https://www.bayshore.ca" + store["url"],
            }

            if "pharmacy" in properties.get("name", "").lower():
                apply_category(Categories.PHARMACY, properties)
            elif (
                "home care" in properties.get("name", "").lower() or "home health" in properties.get("name", "").lower()
            ):
                apply_category({"office": "healthcare"}, properties)
            else:
                apply_category(Categories.CLINIC, properties)

            yield Feature(**properties)
