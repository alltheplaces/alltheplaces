import json

import scrapy
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FluggerNoSpider(scrapy.Spider):
    name = "flugger_no"
    allowed_domains = ["api.flugger.no"]
    item_attributes = {"brand": "Flügger farve", "brand_wikidata": "Q10497241"}

    API_URL = "https://api.flugger.no/stores/b2c?page={page}&loadPrevious=false"
    HEADERS = {
        "Content-Type": "application/json",
        "Pragma": "no-cache",
        "X-Catalog-Id": "fluggerno",
        "X-Forwarded-Host": "www.flugger.no",
        "Accept-Language": "nb-NO",
        "Cache-Control": "no-cache",
        "Origin": "https://www.flugger.no",
        "User-Agent": "Mozilla/5.0 (compatible; AllThePlacesBot/1.0)",
        "Referer": "https://www.flugger.no/",
        "Accept": "application/json, text/plain, */*",
    }
    PAYLOAD = json.dumps({"address": None})

    async def start(self):
        self.logger.debug("Starting Flugger.no spider...")
        yield Request(
            url=self.API_URL.format(page=1),
            method="POST",
            headers=self.HEADERS,
            body=self.PAYLOAD,
            callback=self.parse,
            meta={"page": 1},
            dont_filter=True,
        )

    def parse(self, response):
        self.logger.debug(f"Response status: {response.status}")

        if response.status != 200:
            self.logger.error(f"Failed to fetch data: HTTP {response.status}")
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return

        self.logger.debug(f"Found {len(data.get('result', []))} stores in response")

        for store in data.get("result", []):
            self.logger.debug(f"Processing store: {store.get('name')}")

            store_name = store.get("name")  # The API returns the city name in the name field.
            address = store.get("address", {})
            contact_information = store.get("contactInformation", {})
            opening_hours = store.get("openingHours", {})
            street_address = address.get("streetAddress")
            city = address.get("city")
            postcode = address.get("postalCode")
            latitude = address.get("latitude")
            longitude = address.get("longitude")
            store_id = store.get("id")

            if not all([store_name, street_address, city, postcode, latitude, longitude, store_id]):
                self.logger.debug(f"Skipping incomplete store record: {store}")
                continue

            # Keep `name` as the brand and use `branch` for location specificity.
            branch = store_name
            if store_name and city and store_name == city and street_address:
                branch = f"{store_name} - {street_address}"

            # Extract basic info
            properties = {
                "name": self.item_attributes["brand"],
                "branch": branch,
                "addr_full": street_address,
                "city": city,
                "postcode": postcode,
                "country": "NO",
                "phone": contact_information.get("phoneNumber"),
                "email": contact_information.get("email"),
                "website": f"https://www.flugger.no/st-{store_id}/",
                "lat": latitude,
                "lon": longitude,
                "ref": store_id,
            }
            properties.update(self.item_attributes)
            apply_category(Categories.SHOP_PAINT, properties)

            # Extract opening hours
            oh = OpeningHours()
            for day, hours in opening_hours.get("weekdays", {}).items():
                if hours["isOpen"] and hours.get("openFrom") and hours.get("openTo"):
                    oh.add_range(
                        day=day.lower(),
                        open_time=hours["openFrom"],
                        close_time=hours["openTo"],
                        time_format="%H:%M",
                    )

            yield Feature(
                **properties,
                opening_hours=oh.as_opening_hours(),
            )

        if data.get("hasNext", False):
            next_page = response.meta["page"] + 1
            self.logger.debug(f"Fetching next page: {next_page}")
            yield Request(
                url=self.API_URL.format(page=next_page),
                method="POST",
                headers=self.HEADERS,
                body=self.PAYLOAD,
                callback=self.parse,
                meta={"page": next_page},
                dont_filter=True,
            )
