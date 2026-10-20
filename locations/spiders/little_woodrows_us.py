import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider

# Each bar has a page carrying a schema.org LocalBusiness record with
# coordinates, phone and an amenity list.
#
# Its streetAddress holds the whole address as one string, and its postalCode
# is empty, so both the street and the postcode are taken from that string.
#
# No opening hours are published: the pages only carry a marketing line such as
# "Open until 2am".
#
# No brand:wikidata is set because the chain has no Wikidata item.


class LittleWoodrowsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "little_woodrows_us"
    item_attributes = {"brand": "Little Woodrow's"}
    allowed_domains = ["littlewoodrows.com"]
    sitemap_urls = ["https://littlewoodrows.com/wp-sitemap.xml"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["branch"] = (item.pop("name", None) or "").removeprefix("Little Woodrow's ")
        # The page image is a stock photo of the bar rather than a logo.
        item["image"] = None
        # "Open until 2am" is a marketing line, not a description.
        item["extras"].pop("description", None)

        # "2535 Babcock Rd, San Antonio, TX 78229, USA"
        if address := re.match(r"(.+?),\s*[^,]+,\s*[A-Z]{2}\s+(\d{5})", item.get("street_address") or ""):
            item["street_address"] = address.group(1)
            item["postcode"] = address.group(2)

        for amenity in ld_data.get("amenityFeature") or []:
            if amenity.get("name") == "Backyard":
                apply_yes_no(Extras.OUTDOOR_SEATING, item, bool(amenity.get("value")), False)
            elif amenity.get("name") == "Inside":
                apply_yes_no(Extras.INDOOR_SEATING, item, bool(amenity.get("value")), False)

        apply_category(Categories.BAR, item)

        yield item
