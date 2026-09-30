import logging
import re
from collections.abc import Iterable
from typing import ClassVar, Final, Self

import requests
from scrapy.http import Response
from scrapy.spiders import CrawlSpider, SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DELIMITERS_EN, OpeningHours
from locations.items import Feature

# Pre-compile regexes:
ADDR_RE: Final = re.compile(r"(?P<street_address>.*),\s+(?P<city>.*),\s+MD\s+(?P<postcode>\d{5})")  # Street Address

# This block is for working with Google URLs:
FLOAT_RE: Final = r"\d\.\d+"
# All of Maryland fits in lat 3x lon -7x
LAT_RE: Final = rf"(?P<lat>3{FLOAT_RE})"
LON_RE: Final = rf"(?P<lon>-7{FLOAT_RE})"
# Sometimes it is LAT then LON, sometimes reversed. Always seems to have prefix !Xd where X=1-5
ALT_MAP_RE: Final = re.compile(rf".*?![1-5]d{LON_RE}.*![1-5]d{LAT_RE}!?")
ALT_MAP_RE_REV: Final = re.compile(rf".*?![1-5]d{LAT_RE}.*![1-5]d{LON_RE}!?")

# Regex for a number and then am/pm:
TRAILING_TIME_RE: Final = re.compile(r"\s+\d+\s+([ap]m)", re.IGNORECASE)
# Regex to pull location name (ref) out of URL:
URL_REF_RE: Final = re.compile("locations/(.*?)/")


BAD_BRANCHES: Final = {
    "admin",
    "popup",
    "steam",
}  # Admin branch has no books and the popup/RV don't have fixed addresses


class HowardCountyPublicLibraryMDUSSpider(SitemapSpider, CrawlSpider):
    name: ClassVar[str] = "howard_county_public_library_md_us"
    allowed_domains: ClassVar[list[str]] = ["hclibrary.org"]
    item_attributes: ClassVar[dict[str, str]] = {
        "brand": "Howard County Public Library",
        "brand_wikidata": "Q18152010",
    }
    sitemap_urls: ClassVar[list[str]] = ["https://www.hclibrary.org/branch-sitemap.xml"]
    sitemap_rules: ClassVar[list[tuple[str, str]]] = [
        (r"/locations/", "parse_branch"),
    ]

    def parse_branch(self: Self, response: Response) -> Iterable[Feature | None]:
        """Main parser code for spider"""
        if not (match := URL_REF_RE.search(response.url)) or match[1] in BAD_BRANCHES:
            logging.getLogger("HowardCountyPublicLibraryMDUSSpider").debug("Skipping %s", response.url)
            yield None
        else:
            item = Feature()
            logger = logging.getLogger(f"HowardCountyPublicLibraryMDUSSpider[{match[1]}]")

            item["ref"] = match[1]
            item["name"] = (response.css("h1::text").get() or "").strip()
            item["website"] = response.url

            # Call our helpers
            self._parse_address(response, item)
            self._parse_google_maps(response, item, logger)
            self._parse_hours(response, item)
            self._parse_image(response, item)
            self._parse_telephone(response, item)

            # Final sanity check
            for field in (
                "addr_full",
                "image",
                "lat",
                "opening_hours",
                "phone",
                "street_address",
            ):
                if field not in item:
                    logger.error("Did not parse/set field '%s'", field)

            apply_category(Categories.LIBRARY, item)
            yield item

    def _parse_address(self: Self, response: Response, item: Feature) -> None:
        """Helper to find street address and, if possible, break it down"""
        if addr_full := response.xpath(
            "normalize-space(//li[contains(@class, 'row-address__address')]/div[contains(@class, 'row-address__content')]/p)"
        ).get():
            item["addr_full"] = addr_full
            item["state"] = "MD"
            if match := ADDR_RE.match(addr_full):
                for k, v in match.groupdict().items():
                    item[k] = v

    def _parse_google_maps(self: Self, response: Response, item: Feature, logger: logging.Logger) -> None:
        """Helper to extract lat/lon from Google Maps link"""
        # NOTE: As of 29 Sep 2026, the Google Maps are not centered on the actual locations, so we cannot use locations.google_url.extract_google_position
        if google_loc := response.xpath(
            "normalize-space(//li[contains(@class, 'row-address__address')]/div[contains(@class, 'row-address__content')]/a/@href)"
        ).get():
            # Note: Some (like miller location) use https://maps.app.goo.gl/ shortener
            if google_loc.startswith("https://maps.app.goo.gl/"):
                try:
                    if (redirected := requests.head(google_loc, allow_redirects=True, timeout=5)).ok:
                        google_loc = redirected.url
                except requests.RequestException:
                    logger.exception("Trying to expand %s", google_loc)
            if not google_loc.startswith("https://www.google.com/maps/"):
                logger.error("Invalid redirect to %s", google_loc)
                return
            if (match := ALT_MAP_RE.search(google_loc)) or (match := ALT_MAP_RE_REV.search(google_loc)):
                for k, v in match.groupdict().items():
                    item[k] = float(v)

    def _parse_hours(self: Self, response: Response, item: Feature) -> None:
        """Helper to try to find open hours"""
        if hours := response.xpath("//li[contains(@class, 'row-address__hours')]//p//text()").getall():
            open_hours: Final = OpeningHours()
            # "Sun 1 – 5 pm" is being interpreted as 0100 - 1700
            # Maybe this fix should be in OpeningHours.extract_hours_from_string?
            hours_str = " ".join(
                " ".join(hours).split()
            )  # This rips out all the extra whitespace (lots of useless tabs)
            for delim in DELIMITERS_EN:
                loc = 2
                while True:
                    if (loc := hours_str.find(delim, loc)) == -1:  # No more found
                        break
                    # We have one, back up and check if no am/pm, if an am/pm follows, we duplicate
                    if hours_str[loc - 2].isdigit() and (trailing := TRAILING_TIME_RE.search(hours_str[loc + 1 :])):
                        hours_str = f"{hours_str[:loc]}{trailing[1]} {hours_str[loc:]}"
                    loc += 1

            open_hours.add_ranges_from_string(hours_str)
            if open_hours.as_opening_hours():
                item["opening_hours"] = open_hours

    def _parse_image(self: Self, response: Response, item: Feature) -> None:
        """Helper to try to find an aerial image of the branch"""
        if image := response.xpath("//div[contains(@class, 'text-image-carousel--slider')]/img/@src").getall():
            # Take the first image that has the word "aerial" in it; if none do, then just use the first
            item["image"] = next((img for img in image if "aerial" in img.lower()), image[0])

    def _parse_telephone(self: Self, response: Response, item: Feature) -> None:
        """Helper to try to find a direct telephone number"""
        if telephone := response.xpath('//a[starts-with(@href, "tel:")]/@href').get():
            item["phone"] = telephone.split(":")[1]
