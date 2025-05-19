import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class TomWahlsUSSpider(scrapy.Spider):
    name = "tom_wahls_us"
    item_attributes = {"brand": "Tom Wahl's", "brand_wikidata": "Q7817965"}
    allowed_domains = ["tomwahls.com"]

    # Use custom headers to mimic a real browser (learned from Bill Gray's)
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

    start_urls = ["https://www.tomwahls.com"]

    def parse(self, response):
        # Tom Wahl's has all locations in JSON-LD structured data on the homepage
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            # The locations are nested in the "department" array of the main object
            if departments := ld_obj.get("department"):
                for location in departments:
                    # Filter for FastFoodRestaurant type
                    if not location.get("@type") == "FastFoodRestaurant":
                        continue

                    yield self.parse_location(location)
            # Also check direct FastFoodRestaurant objects
            elif ld_obj.get("@type") == "FastFoodRestaurant":
                yield self.parse_location(ld_obj)

    def parse_location(self, location):
        item = Feature()

        # Extract basic info from JSON-LD
        item["name"] = location.get("name")
        item["website"] = "https://www.tomwahls.com"

        # Extract address info
        address = location.get("address", {})
        item["street_address"] = address.get("streetAddress")
        item["city"] = address.get("addressLocality")
        item["state"] = address.get("addressRegion")
        item["postcode"] = address.get("postalCode")
        item["country"] = address.get("addressCountry", "US")

        # Extract contact info
        phone = location.get("telephone")
        if phone:
            # Clean phone number format
            item["phone"] = phone.replace("+1", "")

        # Extract coordinates safely
        location_data = location.get("location", {})
        geo = location_data.get("geo", {})
        if geo.get("latitude") and geo.get("longitude"):
            item["lat"] = float(geo.get("latitude"))
            item["lon"] = float(geo.get("longitude"))

        # Extract branch name from the full name
        # e.g., "Tom Wahl's Avon" -> branch = "Avon"
        if item["name"] and item["name"].startswith("Tom Wahl's "):
            item["branch"] = item["name"].replace("Tom Wahl's ", "")

        # Set ref based on branch name or city
        item["ref"] = item.get("branch") or item.get("city")

        # Apply category for fast food restaurants
        apply_category(Categories.FAST_FOOD, item)

        # Add burger cuisine
        item["extras"] = {"cuisine": "burger"}

        return item
