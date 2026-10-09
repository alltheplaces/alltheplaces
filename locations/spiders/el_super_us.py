import json
import re
from typing import Any

from scrapy import Selector
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

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
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

        item["branch"] = store_name
        item["ref"] = ref

    def _extract_address(self, response: Response, item: Feature) -> None:
        if address_text := response.xpath('//div[contains(@class, "single-store-info")]//p/text()').get():
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

    def _extract_opening_hours(self, response: Response, item: Feature) -> None:
        if match := re.search(r"singleStore\s*=\s*(\{.*?\});", response.text):
            hours_html = json.loads(match.group(1)).get("hours") or ""
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(" ".join(Selector(text=hours_html).xpath("//text()").getall()))
