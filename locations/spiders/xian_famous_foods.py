import re
from typing import Any, Iterable, Optional, Tuple

import scrapy
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
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

        # Some addresses have newlines, so we need to handle that
        address = address.replace("\n", " ").strip()

        # Extract street address, city, state, and postcode
        # First try the standard format
        address_match = re.search(r"(.*?),\s+(.*?),\s+([A-Z]{2})\s+(\d{5})", address)

        # If that fails, try an alternative format (for addresses like "309 Amsterdam Ave. New York, NY 10023")
        if not address_match:
            address_match = re.search(r"(.*?)\s+([^,]+),\s+([A-Z]{2})\s+(\d{5})", address)

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

    def _parse_hours(self, hours: Optional[str]) -> Optional[str]:
        """Parse hours string into standardized opening hours format."""
        if not hours:
            return None

        # Normalize hours format
        hours = hours.strip()
        if "Every day" in hours:
            time_range = hours.replace("Every day:", "").replace("Every day", "").strip()
            return f"Mo-Su {time_range}"
        elif "Mon-Fri" in hours:
            # Handle more complex hours formats
            hours_parts = hours.split(";")
            weekday_hours = ""
            weekend_hours = ""

            for part in hours_parts:
                part = part.strip()
                if "Mon-Fri" in part:
                    weekday_match = re.search(r"Mon-Fri:\s*([\d:]+)-([\d:]+)", part)
                    if weekday_match:
                        weekday_hours = f"Mo-Fr {weekday_match.group(1)}-{weekday_match.group(2)}"
                elif "Sat&Sun" in part or "Sat & Sun" in part:
                    weekend_match = re.search(r"Sat\s*&\s*Sun\s*:?\s*([\d:]+)-([\d:]+)", part)
                    if weekend_match:
                        weekend_hours = f"Sa-Su {weekend_match.group(1)}-{weekend_match.group(2)}"

            if weekday_hours and weekend_hours:
                return f"{weekday_hours}; {weekend_hours}"
            elif weekday_hours:
                return weekday_hours
            elif weekend_hours:
                return weekend_hours

        return None
