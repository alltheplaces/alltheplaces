import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Location pages are listed in the sitemap alongside the site map directory
# pages, and carry a schema.org Restaurant record with address, coordinates,
# phone and hours.
#
# The record's name is "Goodcents - 1021", which holds the store number.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class GoodcentsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "goodcents_us"
    item_attributes = {"brand": "Goodcents"}
    allowed_domains = ["locations.goodcentssubs.com"]
    sitemap_urls = ["https://locations.goodcentssubs.com/sitemap.xml"]
    sitemap_rules = [(r"/en-us/us/[a-z]{2}/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # "Goodcents - 1021"
        if store_number := re.search(r"(\d+)\s*$", item.get("name") or ""):
            item["ref"] = store_number.group(1)
        item["name"] = None
        item["branch"] = None
        # The same two brand images are used on every page.
        item["image"] = None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"

        yield item
