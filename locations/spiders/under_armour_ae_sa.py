from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class UnderArmourAESASpider(Spider):
    name = "under_armour_ae_sa"
    item_attributes = {
        "brand": "Under Armour",
        "brand_wikidata": "Q2031485",
    }
    allowed_domains = ["underarmour.ae", "underarmour.sa"]

    def start_requests(self):
        urls = [
            # UAE stores
            "https://www.underarmour.ae/on/demandware.store/Sites-UnderArmour_AE-Site/en_AE/Stores-FindStores?showMap=true&selectedCountry=AE&city=all",
            # Saudi Arabia stores
            "https://www.underarmour.sa/on/demandware.store/Sites-UnderArmour_SA-Site/en_SA/Stores-FindStores?showMap=true&selectedCountry=SA&city=all",
        ]

        for url in urls:
            country_code = "SA" if "underarmour.sa" in url else "AE"
            yield JsonRequest(url=url, meta={"country": country_code})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()

        for store in data.get("stores", []):
            item = Feature()

            # Basic store info
            item["ref"] = store.get("ID")
            item["name"] = store.get("name")

            # Location
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")

            # Contact
            phone = store.get("phone", "")
            if phone.startswith("Phone"):
                phone = phone[5:]  # Remove "Phone" prefix if present
            item["phone"] = phone or None

            # Address
            address_parts = []
            if store.get("address1"):
                address_parts.append(store["address1"])
            if store.get("address2"):
                address_parts.append(store["address2"])

            item["street_address"] = ", ".join(address_parts) if address_parts else None
            item["city"] = store.get("city")
            item["state"] = store.get("stateCode")
            item["country"] = store.get("countryCode")

            # Hours
            store_hours = store.get("storeHours", [])
            if store_hours:
                item["opening_hours"] = self.parse_hours(store_hours)

            # Additional properties
            item["extras"] = {
                "shop": "clothes",
                "sport": "running",
            }

            yield item

    def parse_hours(self, hours_data):
        """Convert store hours to OSM format"""
        day_map = {
            "sun": "Su",
            "mon": "Mo",
            "tue": "Tu",
            "wed": "We",
            "thu": "Th",
            "fri": "Fr",
            "sat": "Sa",
        }

        # Group days with the same hours
        hours_by_time = {}
        for day_data in hours_data:
            day = day_data.get("name", "").lower()
            start = day_data.get("start")
            end = day_data.get("end")

            if not (day and start and end):
                continue

            # Handle 24:00 as 00:00
            if end == "24:00":
                end = "00:00"

            # Handle hours past midnight (e.g., 01:00)
            if end < start:
                time_range = f"{start}-24:00,00:00-{end}"
            else:
                time_range = f"{start}-{end}"

            if time_range not in hours_by_time:
                hours_by_time[time_range] = []
            hours_by_time[time_range].append(day_map.get(day, day[:2]))

        # Format the hours string
        hours_parts = []
        for time_range, days in hours_by_time.items():
            # Group consecutive days
            days_groups = []
            current_group = [days[0]]

            for i in range(1, len(days)):
                day_idx = list(day_map.values()).index(days[i - 1])
                next_day_idx = list(day_map.values()).index(days[i])

                if next_day_idx == (day_idx + 1) % 7:  # Check if consecutive, with wrap-around
                    current_group.append(days[i])
                else:
                    days_groups.append(current_group)
                    current_group = [days[i]]

            days_groups.append(current_group)

            # Format each group
            formatted_days = []
            for group in days_groups:
                if len(group) > 2:
                    formatted_days.append(f"{group[0]}-{group[-1]}")
                else:
                    formatted_days.append(",".join(group))

            hours_parts.append(f"{','.join(formatted_days)} {time_range}")

        return "; ".join(hours_parts)
