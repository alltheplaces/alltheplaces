import json
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class RedTagFashionAESASpider(Spider):
    name = "redtag_fashion_ae_sa"
    item_attributes = {
        "brand": "Red Tag",
        "brand_wikidata": "Q132891092",
    }

    def start_requests(self):
        countries = ["Saudi Arabia", "UAE"]
        for country in countries:
            yield Request(
                url=f"https://redtagfashion.com/locations/locations.php?country={country}",
                callback=self.parse,
                meta={"country": country},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        try:
            stores = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON response: {response.text[:200]}")
            return

        for store in stores:
            item = Feature()

            # Basic store info
            item["ref"] = f"{response.meta['country']}_{store['storecode']}"
            item["name"] = store["locname"]

            # Location
            item["lat"] = float(store["lat"]) if store.get("lat") else None
            item["lon"] = float(store["lng"]) if store.get("lng") else None

            # Contact
            item["phone"] = store.get("phone", "").strip() or None
            item["email"] = store.get("email")

            # Address
            item["street_address"] = store.get("address")
            item["city"] = store.get("city")
            item["country"] = store.get("country")

            # Hours
            hours = store.get("timming")  # Note the misspelling in the API
            if hours:
                item["opening_hours"] = self.parse_hours(hours)

            # Additional properties
            item["extras"] = {}
            if store.get("homeware") == "1":
                item["extras"]["homeware"] = True
            if store.get("cosmetics") == "1":
                item["extras"]["cosmetics"] = True

            yield item

    def parse_hours(self, hours_str: str) -> str:
        """Parse hours string into OpenStreetMap format"""
        try:
            if not hours_str:
                return None

            formatted_hours = []

            # Split different day ranges
            for section in hours_str.split("|"):
                section = section.strip()
                if not section:
                    continue

                # Split days and times
                days, times = section.split(" ", 1)
                days = days.strip()
                times = times.strip()

                # Handle "Sun to Thu" format
                if "to" in days:
                    start_day, end_day = days.split(" to ")
                    days = f"{start_day}-{end_day}"
                # Handle "Fri & Sat" format
                elif "&" in days:
                    days = days.replace(" & ", ",")

                # Clean up times
                times = times.replace(" AM", ":00") if "AM" in times else times.replace(" PM", ":00")

                formatted_hours.append(f"{days} {times}")

            return "; ".join(formatted_hours)
        except Exception as e:
            self.logger.warning(f"Could not parse hours: {hours_str} - {e}")
            return None
