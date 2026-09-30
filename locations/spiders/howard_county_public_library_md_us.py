import re
from collections.abc import Iterable
from typing import ClassVar, Final

from scrapy.http import Response
from scrapy.spiders import CrawlSpider, SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DELIMITERS_EN, OpeningHours
from locations.items import Feature

ADDR_RE: Final = re.compile(r"(?P<street_address>.*),\s+(?P<city>.*),\s+MD\s+(?P<postcode>\d{5})")
BAD_COORDINATES: Final[bool] = (
    True  # As of 29 Sep 2026, the Google Maps are not centered on the actual locations, making this information useless
)
BAD_BRANCHES: Final = {
    "admin",
    "popup",
    "steam",
}  # Admin branch has no books and the popup/RV don't have fixed addresses
TRAILING_TIME_RE: Final = re.compile(r"\s+\d+\s+([ap]m)", re.IGNORECASE)
URL_REF_RE: Final = re.compile("locations/(.*?)/")


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

    def parse_branch(self, response: Response) -> Iterable[Feature | None]:
        if not (match := URL_REF_RE.search(response.url)) or match[1] in BAD_BRANCHES:
            yield None
        else:
            item = Feature()

            item["ref"] = match[1]
            item["name"] = (response.css("h1::text").get() or "").strip()
            item["website"] = response.url

            # Telephone
            if telephone := response.xpath('//a[starts-with(@href, "tel:")]/@href').get():
                item["phone"] = telephone.split(":")[1]

            # Hours
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

            # Street Address
            if addr_full := response.xpath(
                "normalize-space(//li[contains(@class, 'row-address__address')]/div[contains(@class, 'row-address__content')]/p)"
            ).get():
                item["addr_full"] = addr_full
                item["state"] = "MD"
                if match := ADDR_RE.match(addr_full):
                    for k, v in match.groupdict().items():
                        item[k] = v

            # Extract lat/lon from Google Map link
            if not BAD_COORDINATES and (
                google_loc := response.xpath(
                    "//li[contains(@class, 'row-address__address')]/div[contains(@class, 'row-address__content')]"
                )
            ):
                extract_google_position(item, google_loc)

            # Unique Image
            if image := response.xpath("//div[contains(@class, 'text-image-carousel--slider')]/img/@src").getall():
                # Take the first image that has the word "aerial" in it; if none do, then just use the first
                item["image"] = next((img for img in image if "aerial" in img.lower()), image[0])

            apply_category(Categories.LIBRARY, item)
            yield item
