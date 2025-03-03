from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class FootLockerAESASpider(Spider):
    name = "footlocker_ae_sa"
    item_attributes = {
        "brand": "Foot Locker",
        "brand_wikidata": "Q63335",
    }
    allowed_domains = ["footlocker.com.sa", "footlocker.ae"]
    start_urls = [
        "https://www.footlocker.com.sa/en/alshaya-locations/stores-list",
        "https://www.footlocker.ae/en/alshaya-locations/stores-list",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()["items"]

        # Determine country from URL
        country = "SA" if "footlocker.com.sa" in response.url else "AE"

        for store in stores:
            item = Feature()

            # Basic store info
            item["ref"] = f"{country}_{store['store_code']}"
            item["name"] = store["store_name"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["phone"] = store.get("store_phone")
            item["email"] = store.get("store_email")

            # Website
            base_url = "https://www.footlocker.com.sa" if country == "SA" else "https://www.footlocker.ae"
            item["website"] = urljoin(f"{base_url}/en/store-finder/", item["ref"])

            # Address components
            address_parts = {part["code"]: part["value"] for part in store["address"]}

            street_parts = []
            if "street" in address_parts:
                street_parts.append(address_parts["street"])
            if "address_building_segment" in address_parts:
                street_parts.append(address_parts["address_building_segment"])
            if "address_apartment_segment" in address_parts:
                street_parts.append(address_parts["address_apartment_segment"])

            item["street_address"] = ", ".join(filter(None, street_parts))
            item["country"] = country

            # Opening hours
            item["opening_hours"] = self.parse_hours(store.get("store_hours", []))

            yield item

    def parse_hours(self, hours_data: list) -> str:
        oh = OpeningHours()

        for hour in hours_data:
            day = hour["label"]
            times = hour["value"].strip()

            # Handle 24 Hours case
            if times == "24 Hours":
                oh.add_range(day, "00:00", "23:59")
                continue

            # Clean up any formatting issues
            times = (
                times.replace(" : ", ":")
                .replace("- ", "-")
                .replace(" to ", "-")
                .replace("AM", " AM")
                .replace("PM", " PM")
                .replace("\u202f", " ")
            )  # Replace thin space with regular space

            # Handle special case for Friday prayer time
            if "pm-" in times:
                times = times.replace("pm-", "pm -")

            try:
                oh.add_range(day, *self.split_hours(times))
            except:
                self.logger.warning(f"Could not parse hours: {times} for {day}")

        return oh.as_opening_hours()

    def split_hours(self, hours_range: str) -> tuple[str, str]:
        """Split hours range into open and close times"""
        start, end = hours_range.split("-")
        start = start.strip()
        end = end.strip()

        # Convert to 24-hour format if needed
        if "am" in start.lower():
            start = start.lower().replace("am", "").strip()
        if "pm" in start.lower():
            if ":" in start:
                hour, minute = start.lower().replace("pm", "").strip().split(":")
                start = f"{int(hour) + 12}:{minute}"
            else:
                start = f"{int(start.lower().replace('pm', '').strip()) + 12}:00"

        if "am" in end.lower():
            end = end.lower().replace("am", "").strip()
        if "pm" in end.lower():
            if ":" in end:
                hour, minute = end.lower().replace("pm", "").strip().split(":")
                end = f"{int(hour) + 12}:{minute}"
            else:
                end = f"{int(end.lower().replace('pm', '').strip()) + 12}:00"

        return start, end
