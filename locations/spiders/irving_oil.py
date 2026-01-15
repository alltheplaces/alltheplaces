import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature

# Canadian provinces/territories - full names to codes
CA_PROVINCES = {
    "Alberta": "AB",
    "British Columbia": "BC",
    "Manitoba": "MB",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Newfoundland": "NL",
    "Northwest Territories": "NT",
    "Nova Scotia": "NS",
    "Nunavut": "NU",
    "Ontario": "ON",
    "Prince Edward Island": "PE",
    "Quebec": "QC",
    "Saskatchewan": "SK",
    "Yukon": "YT",
}

# US states - full names to codes (subset relevant to Irving Oil territory)
US_STATES = {
    "Maine": "ME",
    "New Hampshire": "NH",
    "Vermont": "VT",
    "Massachusetts": "MA",
    "Connecticut": "CT",
    "Rhode Island": "RI",
    "New York": "NY",
    "New Jersey": "NJ",
    "Pennsylvania": "PA",
}

# Canadian postcode pattern: A1A 1A1
CA_POSTCODE_RE = re.compile(r"([A-Za-z]\d[A-Za-z])\s*(\d[A-Za-z]\d)$")
# US ZIP code pattern: 12345 or 12345-6789
US_POSTCODE_RE = re.compile(r"(\d{5})(?:-\d{4})?$")


class IrvingOilSpider(Spider):
    name = "irving_oil"
    start_urls = ["https://www.irvingoil.com/location/geojson"]
    item_attributes = {"brand": "Irving", "brand_wikidata": "Q1673286"}

    def parse_address(self, address_html: str) -> dict:
        """
        Parse Irving Oil address format: "Street<br/>City, State PostalCode"
        Returns dict with street_address, city, state, postcode, country
        """
        result = {
            "street_address": None,
            "city": None,
            "state": None,
            "postcode": None,
            "country": None,
        }

        if not address_html:
            return result

        # Split on <br/> or <br> to separate street from city/state/postcode
        parts = re.split(r"<br\s*/?>", address_html, flags=re.IGNORECASE)
        parts = [p.strip() for p in parts if p.strip()]

        if not parts:
            return result

        if len(parts) >= 2:
            result["street_address"] = parts[0]
            city_state_postcode = parts[1]
        else:
            # Only one part - try to parse it as city/state/postcode
            city_state_postcode = parts[0]

        # Try to extract postcode from the end
        postcode = None
        postcode_match = CA_POSTCODE_RE.search(city_state_postcode)
        if postcode_match:
            postcode = f"{postcode_match.group(1).upper()} {postcode_match.group(2).upper()}"
            city_state_postcode = city_state_postcode[: postcode_match.start()].strip().rstrip(",")
            result["country"] = "CA"
        else:
            postcode_match = US_POSTCODE_RE.search(city_state_postcode)
            if postcode_match:
                postcode = postcode_match.group(1)
                city_state_postcode = city_state_postcode[: postcode_match.start()].strip().rstrip(",")
                result["country"] = "US"

        result["postcode"] = postcode

        # Now parse "City, State" from remaining string
        # Format is typically "City, State" where State is full name
        if "," in city_state_postcode:
            city_part, state_part = city_state_postcode.rsplit(",", 1)
            result["city"] = city_part.strip()
            state_name = state_part.strip()

            # Convert state name to code and determine country
            if state_name in CA_PROVINCES:
                result["state"] = CA_PROVINCES[state_name]
                result["country"] = "CA"
            elif state_name in US_STATES:
                result["state"] = US_STATES[state_name]
                result["country"] = "US"
            elif len(state_name) == 2:
                # Already a code
                result["state"] = state_name.upper()
        else:
            # No comma - might just be a city or malformed
            result["city"] = city_state_postcode.strip() if city_state_postcode.strip() else None

        return result

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            props = location["properties"]
            if props.get("isBigStop"):
                continue

            item = Feature()
            item["ref"] = props["nid"]
            item["geometry"] = location["geometry"]
            item["website"] = response.urljoin(props.get("link", ""))
            item["phone"] = props.get("phone")

            # Use explicit lat/lon from properties if available
            if props.get("lat") and props.get("long"):
                item["lat"] = float(props["lat"])
                item["lon"] = float(props["long"])

            # Parse structured address
            address = self.parse_address(props.get("address", ""))
            item["street_address"] = address["street_address"]
            item["city"] = address["city"]
            item["state"] = address["state"]
            item["postcode"] = address["postcode"]
            item["country"] = address["country"]

            apply_yes_no(Extras.SHOWERS, item, props.get("showers", False))
            apply_yes_no(Extras.CAR_WASH, item, props.get("carWash", False))
            apply_yes_no(Fuel.DIESEL, item, props.get("diesel", False))

            apply_category(Categories.FUEL_STATION, item)

            yield item
