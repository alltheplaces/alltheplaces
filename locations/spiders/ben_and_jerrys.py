import re

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.storefinders.where2getit import Where2GetItSpider

KNOWN_BAD_STORE_UIDS = [147271772]

# Known issues: Opening hours not captured in Portugal locations due to inconsistent formatting


class BenAndJerrysSpider(Where2GetItSpider):
    name = "ben_and_jerrys"
    item_attributes = {"brand": "Ben & Jerry's", "brand_wikidata": "Q816412"}
    api_key = "3D71930E-EC80-11E6-A0AE-8347407E493E"

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if location[day] is None or location["country"] == "PT" or location["uid"] in KNOWN_BAD_STORE_UIDS:
                continue
            else:
                day_hours = location[day].strip().lower()
                if day_hours is not None and day_hours != "" and day_hours != "closed":
                    # Check for the specific "pm - pm" case and skip if matched
                    if day_hours == "pm - pm":
                        continue  # Skip this day

                    try:
                        # Use regex to split by different types of dashes with optional spaces
                        times = re.split(r"\s*[-–—]\s*", day_hours, maxsplit=1)
                        if len(times) == 2:
                            start_time, end_time = times

                            # Normalize AM/PM indicators to uppercase for consistent parsing
                            start_time = start_time.replace("am", "AM").replace("pm", "PM")
                            end_time = end_time.replace("am", "AM").replace("pm", "PM")

                            # Detect the time of day formatting
                            if "AM" in start_time or "PM" in end_time:
                                format_time = "%I:%M%p"
                            else:
                                format_time = "%H:%M"

                            item["opening_hours"].add_range(
                                sanitise_day(day), start_time.strip(), end_time.strip(), format_time
                            )
                        else:
                            # Throw a hard error with item information
                            error_message = (
                                f"Unexpected opening hours format for {day} in item: {item}. Location data: {location}"
                            )
                            raise ValueError(error_message)
                    except ValueError as e:
                        error_message = (
                            f"Unexpected opening hours format for {day} in item: {item}. Location data: {location}"
                        )
                        raise ValueError(error_message) from e

        apply_yes_no(Extras.DELIVERY, item, location["offersdelivery"] == "1", False)

        yield item
