import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider

# The locations page lists every cafe as a card; each links to that cafe's own
# page, which carries a schema.org LocalBusiness record.
#
# Two things about that record need handling: the coordinates are nested under
# "location" rather than on the business itself, so the linked data parser does
# not pick them up, and openingHours is a list of "Monday 6 AM - 3 PM" strings
# rather than schema.org ranges.
#
# Cafes that have not opened yet are labelled "Coming Soon" on their card.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class JustLoveCoffeeCafeUSSpider(StructuredDataSpider):
    name = "just_love_coffee_cafe_us"
    item_attributes = {"brand": "Just Love Coffee Cafe"}
    allowed_domains = ["www.justlovecoffee.com"]
    start_urls = ["https://www.justlovecoffee.com/find-a-location-near-you/"]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for location in response.xpath('//div[contains(@class, "location-card-item")][@data-lat]'):
            if "coming soon" in " ".join(location.xpath(".//text()").getall()).lower():
                continue
            if url := location.xpath('.//a[contains(@href, "justlovecoffee.com")]/@href').get():
                yield response.follow(url, callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # The linked data parser cannot read "Monday 6 AM - 3 PM", so the list
        # is moved out of its way and parsed below.
        ld_data["openingHoursText"] = ld_data.pop("openingHours", None)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.strip("/").rsplit("/", 1)[-1]
        item["branch"] = (item.pop("name", None) or "").removeprefix("Just Love Coffee Cafe - ")
        # The page image is the chain's logo.
        item["image"] = None
        # sameAs is a single string of comma separated links with empty
        # entries, which the linked data parser reads as one Facebook URL.
        item["facebook"] = next(
            (
                link.strip()
                for link in re.split(r"[,\s]+", " ".join(ld_data.get("sameAs") or []))
                if "facebook.com" in link
            ),
            None,
        )

        if geo := (ld_data.get("location") or {}).get("geo"):
            item["lat"] = geo.get("latitude")
            item["lon"] = geo.get("longitude")

        item["opening_hours"] = self.parse_opening_hours(ld_data)

        apply_category(Categories.CAFE, item)
        item["extras"]["cuisine"] = "coffee_shop"

        yield item

    @staticmethod
    def parse_opening_hours(ld_data: dict) -> OpeningHours | None:
        """Parses entries such as "Monday 6 AM - 3 PM"."""
        oh = OpeningHours()

        for rule in ld_data.get("openingHoursText") or []:
            if not (
                match := re.match(
                    r"\s*(\w+)\s+(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", rule, re.I
                )
            ):
                continue
            if not (day := sanitise_day(match.group(1))):
                continue

            oh.add_range(
                day,
                JustLoveCoffeeCafeUSSpider.normalise_time(match.group(2)),
                JustLoveCoffeeCafeUSSpider.normalise_time(match.group(3)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
