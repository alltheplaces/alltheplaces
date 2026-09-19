import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SpringGreenUSSpider(SitemapSpider, StructuredDataSpider):
    name = "spring_green_us"
    item_attributes = {"brand_wikidata": "Q128776141"}  # brand not in NSI yet
    sitemap_urls = ["https://www.spring-green.com/sitemap.xml"]
    # The site publishes one SEO landing page per served town, with many pages
    # sharing the same franchise office's address. The ref below collapses
    # these back down to one item per office; pages with no address (either no
    # LocalBusiness markup, or a defunct out-of-area page) are dropped.
    sitemap_rules = [(r"^https://www\.spring-green\.com/lawn-care-locations/[a-z0-9-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not item.get("street_address"):
            return

        item["ref"] = re.sub(r"[^a-z0-9]", "", (item["street_address"] + item["postcode"]).lower())
        apply_category(Categories.CRAFT_GARDENER, item)
        yield item
