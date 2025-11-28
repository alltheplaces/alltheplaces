import re
from typing import Iterator

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ElSuperUSSpider(SitemapSpider):
    name = "el_super_us"
    item_attributes = {
        "brand": "El Super",
        "brand_wikidata": "Q124810916",
    }
    allowed_domains = ["elsupermarkets.com"]
    sitemap_urls = ["https://elsupermarkets.com/wp-sitemap-posts-store-1.xml"]
    sitemap_rules = [(r"/store/[^/]+/$", "parse_store")]

    def parse_store(self, response: Response) -> Iterator[Feature]:
        item = Feature()

        # Extract basic store info
        self._extract_store_name_and_ref(response, item)

        # Extract address
        self._extract_address(response, item)

        # Extract phone
        self._extract_phone(response, item)

        # Extract coordinates
        self._extract_coordinates(response, item)

        # Extract opening hours
        self._extract_opening_hours(response, item)

        # Set website
        item["website"] = response.url

        # Apply category
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def _extract_store_name_and_ref(self, response: Response, item: Feature) -> None:
        # Extract store name
        store_name = response.xpath('//h1[@class="pad-und-sm"]/text()').get()
        if not store_name:
            store_name = response.xpath('//h1[contains(@class, "invisibile-h1")]/text()').get()

        if not store_name:
            store_name = response.url.split("/")[-2].replace("-", " ").title()

        # Extract reference from URL
        ref = response.url.split("/")[-2]

        item["name"] = store_name
        item["ref"] = ref

    def _extract_address(self, response: Response, item: Feature) -> None:
        address_text = response.xpath('//div[contains(@class, "single-store-info")]//p/text()').get()
        if not address_text:
            # Try to get address from JavaScript data
            js_data = response.xpath('//script[contains(text(), "var storeData")]/text()').get()
            if js_data:
                address_match = re.search(r'"address":"([^"]+)"', js_data)
                if address_match:
                    address_text = address_match.group(1)

        if address_text:
            item["addr_full"] = address_text
            self._parse_address_components(address_text, item)

    def _parse_address_components(self, address_text: str, item: Feature) -> None:
        address_parts = address_text.split(",")
        if len(address_parts) >= 3:
            # Store street address in the correct field
            item["street_address"] = address_parts[0].strip()

            city_part = address_parts[1].strip()
            item["city"] = city_part

            # Handle the remaining parts which may contain state and zip
            # The pattern is typically: City, State, Zipcode
            # But sometimes it can be: City, State, State, Zipcode

            # Extract state from the last parts
            state_match = None
            for part in address_parts[2:]:
                part = part.strip()
                if re.match(r"^[A-Z]{2}$", part):
                    state_match = part
                    item["state"] = state_match
                    break

            # Extract postcode from the last part
            postcode_match = re.search(r"(\d{5}(?:-\d{4})?)", address_parts[-1])
            if postcode_match:
                item["postcode"] = postcode_match.group(1)

        item["country"] = "US"

    def _extract_phone(self, response: Response, item: Feature) -> None:
        phone = response.xpath('//a[contains(@class, "single-store-a") and contains(@href, "tel:")]/text()').get()
        if phone:
            item["phone"] = phone.strip()

    def _extract_coordinates(self, response: Response, item: Feature) -> None:
        # First try to get coordinates from Google Maps directions link
        map_link = response.xpath('//a[contains(@href, "google.com/maps/dir")]/@href').get()
        if map_link:
            coords_match = re.search(r"destination=([-\d.]+),([-\d.]+)", map_link)
            if coords_match:
                item["lat"] = coords_match.group(1)
                item["lon"] = coords_match.group(2)

        # If not found in directions link, try JavaScript data
        if not item.get("lat") or not item.get("lon"):
            self._extract_coordinates_from_js(response, item)

    def _extract_coordinates_from_js(self, response: Response, item: Feature) -> None:
        js_data = response.xpath('//script[contains(text(), "var storeData")]/text()').get()
        if js_data:
            lat_match = re.search(r'"lat":"?([0-9.-]+)"?', js_data)
            lon_match = re.search(r'"lng":"?([0-9.-]+)"?', js_data)
            if lat_match and lon_match:
                lat = lat_match.group(1)
                lon = lon_match.group(1)
                item["lat"] = lat
                item["lon"] = lon

    def _extract_opening_hours(self, response: Response, item: Feature) -> None:
        oh = OpeningHours()

        # Try different methods to extract hours
        if not self._extract_hours_from_list(response, oh):
            if not self._extract_hours_from_open_at(response, oh):
                self._extract_hours_from_js(response, oh)

        # Add opening hours to item if we found any
        opening_hours = oh.as_opening_hours()
        if opening_hours:
            item["opening_hours"] = opening_hours

    def _extract_hours_from_list(self, response: Response, oh: OpeningHours) -> bool:
        hours_elements = response.xpath(
            '//div[contains(@class, "single-store-info")]//ul/li[string-length(text()) > 0]'
        )

        if not hours_elements:
            return False

        day_mapping = {"Mon": "Mo", "Tue": "Tu", "Wed": "We", "Thu": "Th", "Fri": "Fr", "Sat": "Sa", "Sun": "Su"}

        # Pattern to match day and hours like "Tue Feb 25: 7:00 AM - 10:00 PM"
        pattern = r"([A-Za-z]{3})[^:]*:\s*(\d+:\d+\s*[AP]M)\s*-\s*(\d+:\d+\s*[AP]M)"

        found_hours = False
        for hour_elem in hours_elements:
            day_time = hour_elem.xpath("./text()").get()
            if day_time:
                match = re.search(pattern, day_time)
                if match:
                    day_abbr = match.group(1)
                    if day_abbr in day_mapping:
                        day_code = day_mapping[day_abbr]
                        open_time = match.group(2)
                        close_time = match.group(3)
                        oh.add_range(day_code, open_time, close_time, time_format="%I:%M %p")
                        found_hours = True

        return found_hours

    def _extract_hours_from_open_at(self, response: Response, oh: OpeningHours) -> bool:
        open_hours = response.xpath('//div[contains(@class, "open-at")]/h3/text()').get()
        if not open_hours:
            return False

        hours_match = re.search(r"(\d+:\d+\s*[AP]M)\s*-\s*(\d+:\d+\s*[AP]M)", open_hours)
        if not hours_match:
            return False

        open_time = hours_match.group(1)
        close_time = hours_match.group(2)
        # If we only have general hours, apply to all days
        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            oh.add_range(day, open_time, close_time, time_format="%I:%M %p")

        return True

    def _extract_hours_from_js(self, response: Response, oh: OpeningHours) -> bool:
        js_data = response.xpath('//script[contains(text(), "var storeData")]/text()').get()
        if not js_data:
            return False

        hours_match = re.search(r'"hours":\s*(\{[^}]+\})', js_data)
        if not hours_match:
            return False

        hours_json = hours_match.group(1)
        day_matches = re.findall(r'"([^"]+)":\s*"([^"]+)"', hours_json)

        day_mapping = {
            "monday": "Mo",
            "tuesday": "Tu",
            "wednesday": "We",
            "thursday": "Th",
            "friday": "Fr",
            "saturday": "Sa",
            "sunday": "Su",
        }

        found_hours = False
        for day, hours in day_matches:
            if day.lower() in day_mapping:
                day_code = day_mapping[day.lower()]
                hours_match = re.search(r"(\d+:\d+\s*[AP]M)\s*-\s*(\d+:\d+\s*[AP]M)", hours)
                if hours_match:
                    open_time = hours_match.group(1)
                    close_time = hours_match.group(2)
                    oh.add_range(day_code, open_time, close_time, time_format="%I:%M %p")
                    found_hours = True

        return found_hours
