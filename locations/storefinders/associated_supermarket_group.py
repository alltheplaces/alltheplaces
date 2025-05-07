"""Storefinder module for Associated Supermarket Group brands.

This module contains a base class for extracting store locations from
websites using the same store locator system across the Associated
Supermarket Group brands, including Met Foodmarket, Associated Supermarket,
Compare Foods, and Pioneer Supermarket.
"""

import re
import json
from typing import Iterable, List

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AssociatedSupermarketGroupSpider(Spider):
    """Base spider for all Associated Supermarket Group brands.

    This spider implements shared functionality for extracting store data
    from websites that use the same store locator system.

    Attributes:
        allowed_domains: List of domains allowed for crawling.
        start_urls: List containing the URL to start the spider from.
        operator: Name of the operator/parent company.
        operator_wikidata: Wikidata ID of the operator/parent company.
    """

    # Default values can be overridden by child classes
    allowed_domains: List[str] = [
        "www.metfoods.com",
        "www.shopassociated.com",
        "www.shopcomparefoods.com",
        "www.pioneersupermarkets.com",
    ]

    # Set default operator information - can be overridden
    operator = "Associated Supermarket Group"
    operator_wikidata = "Q4809251"

    def start_requests(self):
        """Generate the initial requests to the brand-specific URL."""
        yield Request(url=self.start_urls[0])

    def parse(self, response: Response) -> Iterable[Feature]:
        """Extract store information from the store locator page.

        Args:
            response: The HTTP response containing the store locator HTML.

        Yields:
            Feature objects containing store information.
        """
        # Extract the locations data from JavaScript array in the page
        js_data = response.xpath('//script[contains(text(), "var locations =")]/text()').get()
        store_coords = {}

        if js_data:
            # Extract the JSON array from the JavaScript code
            locations_json = re.search(r"var locations = (\[.*?\]);", js_data, re.DOTALL)
            if locations_json:
                try:
                    locations_data = json.loads(locations_json.group(1))
                    # Create a dictionary to map store_id to coordinates
                    for location in locations_data:
                        store_id = location.get("storeID")
                        if store_id and "latitude" in location and "longitude" in location:
                            store_coords[store_id] = {
                                "lat": float(location["latitude"]),
                                "lon": float(location["longitude"]),
                            }
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse locations JSON data")

        stores = response.css("li.locator-store-item")

        for store in stores:
            store_id = store.attrib.get("data-store", "")
            name = store.css(".locator-store-name::text").get().strip()
            street = store.css(".locator-address::text").get().strip()

            # Extract location information
            info_text = store.css(".locator-storeinformation::text").get().strip()
            city_state_zip_match = re.search(r"([^,]+),\s*([A-Z]{2})\s*(\d{5})", info_text)

            if city_state_zip_match:
                city = city_state_zip_match.group(1).strip()
                state = city_state_zip_match.group(2).strip()
                postal = city_state_zip_match.group(3).strip()
            else:
                city, state, postal = "", "", ""

            phone = store.css(".locator-phonenumber::text").get()
            if phone:
                phone = phone.strip()

            # Extract hours
            hours_text = " ".join(store.css(".locator-storehours::text").getall()).strip()

            # Process hours using the built-in parser
            oh = OpeningHours()
            if hours_text:
                # Clean up the hours text for better parsing
                hours_text = re.sub(r'"', "", hours_text)
                hours_text = hours_text.replace("\n", " ")
                hours_text = hours_text.replace("to", "-")

                # Use the built-in parser
                oh.add_ranges_from_string(hours_text)

            properties = {
                "ref": store_id,
                "name": name,
                "street_address": street,
                "city": city,
                "state": state,
                "postcode": postal,
                "phone": phone,
                "website": response.url,
                "operator": self.operator,
                "operator_wikidata": self.operator_wikidata,
            }

            # Add coordinates from the JavaScript data if available
            if store_id in store_coords:
                properties["lat"] = store_coords[store_id]["lat"]
                properties["lon"] = store_coords[store_id]["lon"]

            if oh.as_opening_hours():
                properties["opening_hours"] = oh.as_opening_hours()

            item = Feature(**properties)
            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
