import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider

# Store pages come from the locator subdomain's gzipped sitemap and carry a
# schema.org CafeOrCoffeeShop record with coordinates and the phone number
# nested inside the address.
#
# Its openingHours is one run-on string, "Su 07:00 - 15:00 Mo 06:00 - 16:00
# ...", which the linked data parser cannot read.


class DunnBrothersCoffeeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dunn_brothers_coffee_us"
    item_attributes = {"brand": "Dunn Brothers Coffee", "brand_wikidata": "Q5315537"}
    allowed_domains = ["locations.dunnbrothers.com"]
    sitemap_urls = ["https://locations.dunnbrothers.com/sitemap/sitemap.xml.gz"]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/([^/]+)\.html$", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # The phone is inside the address, and the hours are a run-on string
        # the linked data parser cannot read.
        ld_data["telephone"] = (ld_data.get("address") or {}).get("telephone")
        ld_data["openingHoursText"] = ld_data.pop("openingHours", None)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # "Coon Rapids MN Coffee Shops | Dunn Brothers Coffee 150"
        if store_number := re.search(r"(\d+)\s*$", item.get("name") or ""):
            item["ref"] = store_number.group(1)
        item["name"] = None
        item["branch"] = None
        # Both image and logo are the brand's header logo, and sameAs holds the
        # chain's own social accounts rather than the shop's.
        item["image"] = None
        item["facebook"] = None

        item["opening_hours"] = self.parse_opening_hours(ld_data)

        apply_category(Categories.CAFE, item)
        item["extras"]["cuisine"] = "coffee_shop"

        yield item

    @staticmethod
    def parse_opening_hours(ld_data: dict) -> OpeningHours | None:
        """Parses "Su 07:00 - 15:00 Mo 06:00 - 16:00 ..." into day ranges."""
        oh = OpeningHours()

        for day, open_time, close_time in re.findall(
            r"(" + "|".join(DAYS) + r")\s+(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", ld_data.get("openingHoursText") or ""
        ):
            oh.add_range(day, open_time, close_time)

        return oh if oh else None
