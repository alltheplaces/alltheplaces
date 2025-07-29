import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BillGraysUSSpider(Spider):
    name = "bill_grays_us"
    item_attributes = {"brand": "Bill Gray's", "brand_wikidata": "Q4908019"}
    allowed_domains = ["billgrays.com"]

    # Use custom headers to mimic a real browser
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    }

    def start_requests(self):
        # Start with the locations page
        yield Request(url="https://www.billgrays.com/index.cfm?Page=Locations", callback=self.parse_locations)

    def parse_locations(self, response):
        # Extract location links from the page
        location_links = response.css('a[href*="index.cfm?Page="]::attr(href)').getall()

        # Filter for location pages based on known patterns
        for link in location_links:
            if "Page=" in link:
                page_name = link.split("Page=")[-1]
                # Known Bill Gray's location pages (including tap rooms)
                location_names = [
                    "Brockport",
                    "Bushnells-Basin",
                    "Canandaigua",
                    "Honeoye-Falls",
                    "Henrietta",
                    "Irondequoit",
                    "Penfield",
                    "Port-Of-Rochester",
                    "Sea-Breeze",
                    "Strong",
                    "Webster",
                    "Buffalo",
                    "Chili",
                    "Clarence",
                    "Niagara-Falls",
                    "Parma",
                    "Ontario",
                    "Greece",
                ]
                tap_room_names = [
                    "Brockport-Tap-Room",
                    "Chili-Tap-Room",
                    "North-Greece-Road-Tap-Room",
                    "Ontario-Tap-Room",
                    "Port-Of-Rochester-Tap-Room",
                    "Seabreeze-Tap-Room",
                ]

                if any(loc.lower() in page_name.lower() for loc in location_names + tap_room_names):
                    yield response.follow(link, callback=self.parse_location)

    def parse_location(self, response):
        item = Feature()

        # Extract branch name from URL
        page_param = response.url.split("Page=")[-1]
        item["ref"] = page_param

        # Determine if this is a tap room
        is_tap_room = "Tap-Room" in page_param

        if is_tap_room:
            self._setup_tap_room(item, page_param)
        else:
            item["branch"] = page_param.replace("-", " ")
            apply_category(Categories.FAST_FOOD, item)

        # Extract name from h1
        item["name"] = response.css("h1::text").get() or "Bill Gray's"

        # Extract location data
        location_content = response.css("div.loc-col1.contentnorm").get()
        additional_info = response.css("div.loc-col2.contentnorm").get()

        if location_content:
            self._parse_location_content(item, location_content)

        # Extract amenities for non-tap-room locations
        if additional_info and not is_tap_room:
            self._parse_amenities(item, additional_info)

        # Fallback extraction from meta description
        if not item.get("street_address"):
            self._parse_from_meta(item, response)

        # Extract coordinates from Google Maps link
        extract_google_position(item, response)

        # Set defaults
        item["country"] = "US"
        if not item.get("state"):
            item["state"] = "NY"
        item["website"] = response.url

        yield item

    def _setup_tap_room(self, item, page_param):
        """Configure tap room specific attributes"""
        parent_ref = page_param.replace("-Tap-Room", "")
        item["extras"]["located_in"] = parent_ref
        item["branch"] = page_param.replace("-", " ")
        item["extras"]["tap_room"] = "yes"
        apply_category(Categories.BAR, item)

    def _parse_location_content(self, item, location_content):
        """Parse address, phone, and hours from location content"""
        # Extract address
        address_match = re.search(r"Address:</b><br\s*/><a[^>]*>(.*?)</a>", location_content, re.DOTALL)
        if address_match:
            self._parse_address(item, address_match.group(1))

        # Extract phone
        phone_match = re.search(r"Phone:</b><br\s*/><a[^>]*>([^<]+)</a>", location_content)
        if phone_match:
            item["phone"] = phone_match.group(1).strip()

        # Extract hours
        hours_match = re.search(r"Hours:</b><br\s*/>(.*?)(?:<br\s*/><br\s*/>|</div>)", location_content, re.DOTALL)
        if hours_match:
            hours_text = hours_match.group(1).replace("<br />", " ").replace("<br/>", " ").strip()
            item["opening_hours"] = self.parse_hours(hours_text)

        # Extract patio seating status
        patio_match = re.search(r"Patio Seating is <b>(OPEN|CLOSED)</b>", location_content)
        if patio_match:
            item["extras"]["outdoor_seating_status"] = patio_match.group(1).lower()

    def _parse_address(self, item, address_html):
        """Parse address components from HTML"""
        address_lines = address_html.replace("<br />", ", ").replace("<br/>", ", ").strip()
        address_parts = address_lines.split(",")

        if len(address_parts) >= 2:
            item["street_address"] = address_parts[0].strip()
            city_state_zip = ",".join(address_parts[1:]).strip()

            # Parse city, state, zip
            city_state_zip_match = re.match(r"^(.*?),?\s*([A-Z]{2})\s*(\d{5})$", city_state_zip)
            if city_state_zip_match:
                item["city"] = city_state_zip_match.group(1).strip()
                item["state"] = city_state_zip_match.group(2)
                item["postcode"] = city_state_zip_match.group(3)
            else:
                # Alternative pattern
                parts = city_state_zip.split()
                if len(parts) >= 3 and len(parts[-1]) == 5 and parts[-1].isdigit():
                    item["postcode"] = parts[-1]
                    item["state"] = parts[-2] if len(parts[-2]) == 2 else "NY"
                    item["city"] = " ".join(parts[:-2])
                elif len(parts) >= 2:
                    item["state"] = parts[-1] if len(parts[-1]) == 2 else "NY"
                    item["city"] = " ".join(parts[:-1])

    def _parse_amenities(self, item, additional_info):
        """Parse amenities from the second column"""
        # Extract Abbott's availability
        abbotts_match = re.search(r"Abbott\\'?s?:</b><br\s*/>\s*(Yes|No|yes|no)", additional_info)
        if abbotts_match:
            item["extras"]["serves_frozen_custard"] = "yes" if abbotts_match.group(1).lower() == "yes" else "no"

        # Extract outdoor seating
        outdoor_match = re.search(r"Outdoor\s+Seating:</b><br\s*/>\s*(Yes|No|yes|no)", additional_info)
        if outdoor_match:
            item["extras"]["outdoor_seating"] = "yes" if outdoor_match.group(1).lower() == "yes" else "no"

        # Extract party room availability
        party_match = re.search(r"Party\s+Room:</b><br\s*/>\s*(Yes|No|yes|no)", additional_info)
        if party_match:
            item["extras"]["private_events"] = "yes" if party_match.group(1).lower() == "yes" else "no"

        # Extract general manager
        gm_match = re.search(r"General\s+Manager:</b><br\s*/>\s*(.*?)(?:</div>|<br|$)", additional_info)
        if gm_match:
            item["extras"]["general_manager"] = gm_match.group(1).strip()

    def _parse_from_meta(self, item, response):
        """Fallback parsing from meta description"""
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        if meta_desc:
            # Pattern: "... Address: 1225 Jefferson Rd Rochester, NY 14623 ..."
            addr_match = re.search(r"Address:\s*([^,]+),?\s+([^,]+),?\s+([A-Z]{2})\s+(\d{5})", meta_desc)
            if addr_match:
                item["street_address"] = addr_match.group(1).strip()
                item["city"] = addr_match.group(2).strip()
                item["state"] = addr_match.group(3)
                item["postcode"] = addr_match.group(4)

            # Extract phone from meta
            phone_match = re.search(r"Phone:\s*([\d-]+)", meta_desc)
            if phone_match:
                item["phone"] = phone_match.group(1)

            # Extract hours from meta
            hours_match = re.search(r"Hours:\s*(.*?)(?:\s*P|$)", meta_desc)
            if hours_match:
                hours_text = hours_match.group(1) + ("" if hours_match.group(0).endswith("$") else "P")
                item["opening_hours"] = self.parse_hours(hours_text)

    def parse_hours(self, hours_text):
        """Parse hours text into OpeningHours object"""
        try:
            oh = OpeningHours()

            # Clean up the text
            hours_text = re.sub(r"\s+", " ", hours_text).strip()

            # Fix time format - convert "11:00am" to "11:00 AM"
            hours_text = re.sub(r"(\d{1,2}:\d{2})\s*([ap])m", r"\1 \2m", hours_text, flags=re.IGNORECASE)
            hours_text = hours_text.lower().replace("am", "AM").replace("pm", "PM")

            # Pattern for "Sunday - Thursday: 11:00 AM to 9:00 PM"
            range_pattern = r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))\s*[-–]\s*((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*to\s*(\d{1,2}:\d{2}\s*[AP]M)"
            matches = re.finditer(range_pattern, hours_text, re.IGNORECASE)

            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

            for match in matches:
                start_day, end_day, open_time, close_time = match.groups()
                start_day = start_day.capitalize()
                end_day = end_day.capitalize()

                # Normalize time format
                open_time = open_time.strip()
                close_time = close_time.strip()

                # Get day indices
                start_idx = days_order.index(start_day)
                end_idx = days_order.index(end_day)

                # Add range for each day
                if start_idx <= end_idx:
                    for i in range(start_idx, end_idx + 1):
                        oh.add_range(days_order[i], open_time, close_time, time_format="%I:%M %p")
                else:  # Wrap around (e.g., Friday - Monday)
                    for i in range(start_idx, 7):
                        oh.add_range(days_order[i], open_time, close_time, time_format="%I:%M %p")
                    for i in range(0, end_idx + 1):
                        oh.add_range(days_order[i], open_time, close_time, time_format="%I:%M %p")

            # Also handle single day patterns like "Friday & Saturday: 11:00 AM to 9:00 PM"
            single_pattern = r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))(?:\s*&\s*((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*to\s*(\d{1,2}:\d{2}\s*[AP]M)"
            matches = re.finditer(single_pattern, hours_text, re.IGNORECASE)

            for match in matches:
                groups = match.groups()
                day1 = groups[0].capitalize()
                open_time = groups[2].strip()
                close_time = groups[3].strip()
                oh.add_range(day1, open_time, close_time, time_format="%I:%M %p")
                if groups[1]:  # Second day in "Friday & Saturday"
                    day2 = groups[1].capitalize()
                    oh.add_range(day2, open_time, close_time, time_format="%I:%M %p")

            return oh if oh else None
        except Exception:
            # If hours parsing fails, return None rather than crashing
            return None
