import re
from typing import Any, Iterable, List, Optional, Tuple

import scrapy
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class XianFamousFoodsSpider(scrapy.Spider):
    name = "xian_famous_foods"
    item_attributes = {
        "brand": "Xi'an Famous Foods",
        "brand_wikidata": "Q8044020",
        "extras": Categories.RESTAURANT.value,
    }
    allowed_domains = ["xianfoods.com"]
    start_urls = ["https://www.xianfoods.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        """Parse the locations page to extract store information."""
        # The page is organized by region (Manhattan, Brooklyn, Queens)
        for borough_container in response.css(".page-locations_borough-container"):
            borough = borough_container.css(".page-locations_borough-title::text").get()

            # Process each location item within this borough
            for location_item in borough_container.css(".page-location_location-item"):
                location_data = self._extract_location_data(response, location_item, borough)
                if location_data:
                    yield location_data

    def _extract_location_data(self, response: Response, location_item: Selector, borough: str) -> Optional[Feature]:
        """Extract data for a single location."""
        # Extract location name (neighborhood)
        location_name = location_item.css(".location-name::text").get()
        if not location_name:
            return None

        # Extract address and hours
        address = self._get_text_from_detail(location_item, 0)
        if not address:
            return None

        hours = self._get_text_from_detail(location_item, 1)

        # Parse address components
        address_components = self._parse_address(address)
        if not address_components:
            return None

        street_address, city, state, postcode = address_components

        # Extract coordinates
        lat, lon = self._extract_coordinates(response, location_name)

        # Parse hours
        opening_hours = self._parse_hours(hours)

        # Create a unique reference ID
        ref = f"{borough.lower()}-{location_name.lower().replace(' ', '-')}"

        # Create the store item
        item = Feature(
            ref=ref,
            name=f"Xi'an Famous Foods - {location_name.strip()}",
            street_address=street_address,
            city=city,
            state=state,
            postcode=postcode,
            country="US",
            lat=lat,
            lon=lon,
            website="https://www.xianfoods.com/locations",
            opening_hours=opening_hours,
        )

        # Apply restaurant category
        apply_category(Categories.RESTAURANT, item)

        # Add cuisine information
        item["extras"]["cuisine"] = "chinese"

        # Add takeaway information (all locations offer takeaway)
        item["extras"]["takeaway"] = "yes"

        return item

    def _get_text_from_detail(self, location_item: Selector, index: int) -> Optional[str]:
        """Extract text from a location detail element at the given index."""
        detail_elements = location_item.css(".location-detail_copy")
        if len(detail_elements) > index:
            return detail_elements[index].css("::text").get()
        return None

    def _parse_address(self, address: str) -> Optional[Tuple[str, str, str, str]]:
        """Parse an address string into components."""
        if not address:
            return None

        # Clean up the address by replacing multiple whitespaces and newlines with a single space
        address = re.sub(r"\s+", " ", address.replace("\n", " ")).strip()

        # Check for the specific Amsterdam Ave. case
        amsterdam_match = re.search(r"((\d+)\s+Amsterdam Ave\.)\s+(New York),\s+([A-Z]{2})\s+(\d{5})", address)
        if amsterdam_match:
            street_address = amsterdam_match.group(1).strip()
            city = amsterdam_match.group(3).strip()
            state = amsterdam_match.group(4)
            postcode = amsterdam_match.group(5)
            return street_address, city, state, postcode

        # Extract street address, city, state, and postcode
        # First try the standard format
        address_match = re.search(r"(.*?),\s+(.*?),\s+([A-Z]{2})\s+(\d{5})", address)

        # If that fails, try an alternative format (for addresses like "309 Amsterdam Ave. New York, NY 10023")
        if not address_match:
            address_match = re.search(r"(.*?)\s+([^,]+),\s+([A-Z]{2})\s+(\d{5})", address)

        # If that still fails, try a more flexible format to handle addresses with or without periods
        if not address_match:
            address_match = re.search(
                r"(.*?(?:Ave|St|Pl|Rd|Blvd|Dr|Ln|Ct|Way)\.?)\s+([^,]+),\s+([A-Z]{2})\s+(\d{5})", address, re.IGNORECASE
            )

        if not address_match:
            self.logger.warning(f"Could not parse address: {address}")
            return None

        street_address = address_match.group(1).strip()
        city = address_match.group(2).strip()
        state = address_match.group(3)
        postcode = address_match.group(4)

        return street_address, city, state, postcode

    def _extract_coordinates(self, response: Response, location_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract coordinates for a location from the map data."""
        location_data = response.css(f'.location-data[data-name="{location_name}"]')
        lat = lon = None
        if location_data:
            lat = location_data.attrib.get("data-lat")
            lon = location_data.attrib.get("data-lng")
        return lat, lon

    def _normalize_time(self, time_str: str) -> str:
        """Normalize time string to HH:MM format."""
        time_str = time_str.strip()

        # Add colon if missing
        if ":" not in time_str:
            time_str = f"{time_str}:00"

        return time_str

    def _convert_to_24h_format(self, open_time: str, close_time: str) -> Tuple[str, str]:
        """Convert times to 24-hour format if needed."""
        # If close time is less than open time or single digit, assume it's PM
        if len(close_time.split(":")[0]) == 1 or int(close_time.split(":")[0]) < int(open_time.split(":")[0]):
            close_hour = int(close_time.split(":")[0])
            close_minute = close_time.split(":")[1]
            close_time = f"{close_hour + 12}:{close_minute}"

        return open_time, close_time

    def _add_time_range(self, opening_hours: OpeningHours, days: List[str], open_time: str, close_time: str) -> None:
        """Add a time range for the specified days."""
        open_time = self._normalize_time(open_time)
        close_time = self._normalize_time(close_time)

        open_time, close_time = self._convert_to_24h_format(open_time, close_time)

        for day in days:
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

    def _handle_everyday_hours(self, opening_hours: OpeningHours, hours: str) -> bool:
        """Handle 'Every day' format hours."""
        if "Every day" not in hours:
            return False

        time_range = hours.replace("Every day:", "").replace("Every day", "").strip()
        if "-" not in time_range:
            return False

        open_time, close_time = time_range.split("-")
        self._add_time_range(opening_hours, ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"], open_time, close_time)
        return True

    def _handle_weekday_weekend_hours(self, opening_hours: OpeningHours, hours: str) -> bool:
        """Handle hours with different weekday and weekend schedules."""
        if "Mon-Fri" not in hours:
            return False

        hours_parts = hours.split(";")

        for part in hours_parts:
            part = part.strip()
            if "Mon-Fri" in part:
                weekday_match = re.search(r"Mon-Fri:\s*([\d:]+)-([\d:]+)", part)
                if weekday_match:
                    open_time = weekday_match.group(1)
                    close_time = weekday_match.group(2)
                    self._add_time_range(opening_hours, ["Mo", "Tu", "We", "Th", "Fr"], open_time, close_time)
            elif "Sat&Sun" in part or "Sat & Sun" in part:
                weekend_match = re.search(r"Sat\s*&\s*Sun\s*:?\s*([\d:]+)-([\d:]+)", part)
                if weekend_match:
                    open_time = weekend_match.group(1)
                    close_time = weekend_match.group(2)
                    self._add_time_range(opening_hours, ["Sa", "Su"], open_time, close_time)

        return True

    def _handle_closed_weekends(self, opening_hours: OpeningHours, hours: str) -> bool:
        """Handle locations closed on weekends."""
        if "Closed" not in hours:
            return False

        closed_match = re.search(r"Mon-Fri:\s*([\d:]+)-([\d:]+),\s*Sat\s*&\s*Sun:\s*Closed", hours)
        if not closed_match:
            return False

        open_time = closed_match.group(1)
        close_time = closed_match.group(2)

        self._add_time_range(opening_hours, ["Mo", "Tu", "We", "Th", "Fr"], open_time, close_time)

        # Mark weekends as closed
        opening_hours.set_closed(["Sa", "Su"])
        return True

    def _parse_hours(self, hours: Optional[str]) -> Optional[str]:
        """Parse hours string into standardized opening hours format."""
        if not hours:
            return None

        # Create an OpeningHours object
        opening_hours = OpeningHours()

        # Normalize hours format
        hours = hours.strip()

        # Try each hours format handler
        if self._handle_everyday_hours(opening_hours, hours):
            pass
        elif self._handle_weekday_weekend_hours(opening_hours, hours):
            pass
        elif self._handle_closed_weekends(opening_hours, hours):
            pass
        else:
            self.logger.warning(f"Could not parse hours: {hours}")
            return None

        # Return the formatted opening hours string
        return opening_hours.as_opening_hours() if opening_hours else None
