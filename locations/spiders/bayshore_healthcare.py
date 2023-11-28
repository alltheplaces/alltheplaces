import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


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
            full_addr = store["address"]
            addr = re.search(r"^(.*?)<", full_addr).groups()[0]
            city = re.search(r">(.*?),", full_addr).groups()[0]
            state = re.search(r",\s([A-Z]{2})\s", full_addr).groups()[0]
            postal = re.search(r",\s[A-Z]{2}\s(.*)$", full_addr).groups()[0]

            coords = store["latlng"].split(",")
            lat = coords[0]
            lng = coords[1]

            properties = {
                "ref": store["id"],
                "name": store["name"],
                "street_address": addr,
                "city": city,
                "state": state,
                "postcode": postal,
                "country": "CA",
                "lat": lat,
                "lon": lng,
                "phone": store["local_telephone"],
                "website": "https://www.bayshore.ca" + store["url"],
            }

            if "pharmacy" in properties.get("name", "").lower():
                apply_category(Categories.PHARMACY, properties)
            elif "clinic" in properties.get("name", "").lower():
                apply_category(Categories.CLINIC, properties)
            elif (
                "home care" in properties.get("name", "").lower() or "home health" in properties.get("name", "").lower()
            ):
                # All the others are Home Health Offices - Office to sign up or buy in home health services
                apply_category({"office": "healthcare"}, properties)

            yield Feature(**properties)
