import json
import re

from scrapy import Request
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AbbottsFrozenCustardUSSpider(SitemapSpider):
    name = "abbotts_frozen_custard_us"
    item_attributes = {
        "brand": "Abbott's Frozen Custard",
        "brand_wikidata": "Q4664334",
    }
    allowed_domains = ["abbottscustard.com"]
    sitemap_urls = ["https://www.abbottscustard.com/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/location/", "parse")]
    user_agent = BROWSER_DEFAULT

    # State centroids for Abbott's locations
    # Based on states mentioned in get_state_abbrev
    state_centroids = {
        "NY": {"lat": 43.0, "lon": -76.0},  # New York
        "MA": {"lat": 42.4, "lon": -71.4},  # Massachusetts
        "FL": {"lat": 27.8, "lon": -81.8},  # Florida
        "TX": {"lat": 31.0, "lon": -99.0},  # Texas
        "LA": {"lat": 30.5, "lon": -91.1},  # Louisiana
        "SC": {"lat": 33.8, "lon": -80.5},  # South Carolina
        "NC": {"lat": 35.5, "lon": -79.0},  # North Carolina
        "TN": {"lat": 35.5, "lon": -86.0},  # Tennessee
    }

    def start_requests(self):
        # Initialize coordinate storage
        self.coordinates = {}

        # Make API calls for each state where Abbott's operates
        for state, coords in self.state_centroids.items():
            ajax_url = (
                f"https://www.abbottscustard.com/wp-admin/admin-ajax.php?"
                f"action=store_search&lat={coords['lat']}&lng={coords['lon']}&max_results=100&search_radius=300"
            )
            yield Request(
                url=ajax_url,
                headers={"X-Requested-With": "XMLHttpRequest", "Accept": "*/*"},
                callback=self.parse_locations_data,
                dont_filter=True,
                meta={"state": state},
            )

    def parse_locations_data(self, response):
        """Parse location data from AJAX endpoint to store coordinates"""
        state = response.meta.get("state")

        try:
            locations = json.loads(response.text)
            for location in locations:
                # Get the slug from the permalink
                permalink = location.get("permalink", "")
                if "/location/" in permalink:
                    slug = permalink.split("/location/")[-1].rstrip("/")
                    # Avoid duplicates by checking if we've already stored this location
                    if slug not in self.coordinates:
                        self.coordinates[slug] = {"lat": location.get("lat"), "lon": location.get("lng")}
            self.logger.info(f"Found {len(locations)} locations for state {state}")
        except Exception as e:
            self.logger.error(f"Error parsing JSON for state {state}: {e}")

        # After all state requests are complete, proceed with sitemap crawl
        # (This is handled by Scrapy's scheduler)
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def parse(self, response):
        item = Feature()

        # Extract unique identifier from URL
        item["ref"] = response.url.split("/")[-2]
        item["website"] = response.url

        # Extract store name - usually in H1
        name = response.xpath("//h1/text()").get()
        if name:
            item["name"] = name.strip()

        # Extract all text content to find structured data
        all_text = response.xpath("//body//text()").getall()
        clean_text = [text.strip() for text in all_text if text.strip()]

        # Parse different sections
        self._parse_address_section(item, clean_text)
        self._parse_phone_section(item, clean_text)
        self._parse_hours_section(item, clean_text)

        # Set country
        item["country"] = "US"

        # Add coordinates from AJAX data
        self._add_coordinates(item)

        # All Abbott's locations are ice cream shops
        apply_category(Categories.ICE_CREAM, item)

        # Add parent venue information for locations inside other restaurants
        self._set_located_in(item)

        yield item

    def _parse_address_section(self, item, clean_text):
        """Parse address information from text"""
        for i, text in enumerate(clean_text):
            if text == "Address" and i + 2 < len(clean_text):
                # Next two lines should be street and city/state/zip
                item["street_address"] = clean_text[i + 1]
                city_state_zip = clean_text[i + 2]

                # Parse city, state, zip
                # Pattern: "Fairport, New York 14450"
                match = re.match(r"^(.*?),\s*([A-Za-z\s]+)\s+(\d{5})$", city_state_zip)
                if match:
                    item["city"] = match.group(1).strip()
                    state = match.group(2).strip()
                    if len(state) == 2:
                        item["state"] = state
                    else:
                        item["state"] = self.get_state_abbrev(state)
                    item["postcode"] = match.group(3)
                break

    def _parse_phone_section(self, item, clean_text):
        """Parse phone information from text"""
        for i, text in enumerate(clean_text):
            if text == "Phone" and i + 1 < len(clean_text):
                phone_text = clean_text[i + 1]
                # Clean phone number and format
                phone_digits = re.sub(r"[^\d]", "", phone_text)
                if len(phone_digits) == 10:
                    item["phone"] = f"{phone_digits[:3]}-{phone_digits[3:6]}-{phone_digits[6:]}"
                break

    def _parse_hours_section(self, item, clean_text):
        """Parse store hours from text"""
        for i, text in enumerate(clean_text):
            if text == "Store Hours":
                # Check if it's "Call store for details"
                if i + 1 < len(clean_text) and "Call store" in clean_text[i + 1]:
                    break

                # Parse hours
                oh = self._extract_hours(clean_text, i + 1)
                if str(oh):  # Check if any hours were added
                    item["opening_hours"] = oh
                break

    def _extract_hours(self, clean_text, start_index):
        """Extract hours from text starting at given index"""
        oh = OpeningHours()
        j = start_index
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        while j < len(clean_text) and clean_text[j] in days:
            day = clean_text[j]
            if j + 1 < len(clean_text):
                time_text = clean_text[j + 1]
                # Pattern: "12:00 PM - 8:00 PM"
                time_match = re.match(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", time_text)
                if time_match:
                    open_time, close_time = time_match.groups()
                    # Add time format to match the spaces in the time string
                    oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
                    j += 2  # Skip to next day
                else:
                    j += 1
            else:
                j += 1

        return oh

    def _add_coordinates(self, item):
        """Add coordinates from AJAX data"""
        if hasattr(self, "coordinates") and item["ref"] in self.coordinates:
            coords = self.coordinates[item["ref"]]
            if coords.get("lat") and coords.get("lon"):
                try:
                    item["lat"] = float(coords["lat"])
                    item["lon"] = float(coords["lon"])
                except (ValueError, TypeError):
                    pass

    def _set_located_in(self, item):
        """Set parent venue information for locations inside other restaurants"""
        ref = item["ref"].lower()
        name_lower = item.get("name", "").lower()

        if "bill-grays" in ref or "bill gray" in name_lower:
            item["located_in"] = "Bill Gray's"
            item["located_in_wikidata"] = "Q4909199"
        elif "tom-wahls" in ref or "tom wahl" in name_lower:
            item["located_in"] = "Tom Wahl's"
            item["located_in_wikidata"] = "Q7817965"

    def get_state_abbrev(self, state_name):
        """Convert full state name to abbreviation"""
        states = {
            "new york": "NY",
            "massachusetts": "MA",
            "florida": "FL",
            "texas": "TX",
            "louisiana": "LA",
            "south carolina": "SC",
            "north carolina": "NC",
            "tennessee": "TN",
        }
        return states.get(state_name.lower())
