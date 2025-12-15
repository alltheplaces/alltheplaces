from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class CashBESpider(Spider):
    name = "cash_be"
    item_attributes = {
        "brand": "Bancontact CASH",
        "brand_wikidata": "Q112875867",
        "operator": "Batopin",
        "operator_wikidata": "Q97142699",
    }
    start_urls = ["https://cash.be/nl/locations"]

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        data = response.json()
        for location in data["data"]["locations"]:
            # Skip planned and wanted locations, only include open ones
            if location.get("status") != "OPEN":
                continue

            item = DictParser.parse(location)
            item["ref"] = location.get("shop_code")
            item["street_address"] = location.get("adr_street_nl")
            if housenumber := location.get("adr_street_number"):
                item["housenumber"] = housenumber
            item["postcode"] = location.get("adr_zipcode")
            item["city"] = location.get("adr_city_nl")
            item["country"] = location.get("adr_country")
            item["lat"] = location.get("adr_latitude")
            item["lon"] = location.get("adr_longitude")
            item["phone"] = location.get("phone_number")
            item["website"] = location.get("website")

            # Use Dutch name by default
            item["name"] = location.get("location_name_nl")

            # Add multilingual names and address fields to extras
            for lang in ["nl", "fr", "de", "en"]:
                if name := location.get(f"location_name_{lang}"):
                    item["extras"][f"name:{lang}"] = name
                if street := location.get(f"adr_street_{lang}"):
                    item["extras"][f"addr:street:{lang}"] = street
                if city := location.get(f"adr_city_{lang}"):
                    item["extras"][f"addr:city:{lang}"] = city

            # Parse opening hours
            if regular_hours := location.get("regular_hours"):
                if isinstance(regular_hours, dict) and regular_hours:
                    item["opening_hours"] = self.parse_opening_hours(regular_hours)

            # Parse special hours
            if special_hours := location.get("special_hours_nl"):
                if special_hours.strip():
                    item["extras"]["opening_hours:note"] = special_hours

            # Apply category
            apply_category(Categories.ATM, item)

            # Add ATM features
            apply_yes_no(Extras.CASH_IN, item, location.get("deposit_cash") == "1")

            # Add accessibility info
            if accessibility := location.get("accessibility"):
                accessibility_map = {
                    "Green": "yes",
                    "Orange": "limited",
                    "Red": "no",
                }
                if wheelchair := accessibility_map.get(accessibility):
                    item["extras"]["wheelchair"] = wheelchair

            # Add denomination availability
            denomination_fields = ["5_eur", "10_eur", "20_eur", "50_eur", "100_eur"]
            denominations = [
                field.replace("_eur", "") for field in denomination_fields if location.get(field) == "1"
            ]
            if denominations:
                item["extras"]["currency:EUR"] = ";".join(denominations)

            yield item

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
        """Parse opening hours from the regular_hours dictionary."""
        oh = OpeningHours()
        day_mapping = {
            "MO": "Mo",
            "TU": "Tu",
            "WE": "We",
            "TH": "Th",
            "FR": "Fr",
            "SA": "Sa",
            "SU": "Su",
        }

        for day, times in hours.items():
            if not times or not isinstance(times, str):
                continue

            day_short = day_mapping.get(day)
            if not day_short:
                continue

            # Handle 24/7 format
            if times == "00:00-00:00":
                oh.add_range(day_short, "00:00", "24:00")
            # Handle single time range
            elif "-" in times and ":" in times:
                try:
                    # Extract HH:MM-HH:MM format
                    parts = times.split("-")
                    if len(parts) == 2:
                        start = parts[0].strip()
                        end = parts[1].strip()
                        # Validate time format
                        if ":" in start and ":" in end:
                            oh.add_range(day_short, start, end)
                except Exception:
                    # Skip malformed opening hours
                    pass

        return oh
