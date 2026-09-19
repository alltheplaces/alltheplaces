from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RotoRooterUSSpider(SitemapSpider, StructuredDataSpider):
    name = "roto_rooter_us"
    item_attributes = {"brand_wikidata": "Q7370555"}  # brand not in NSI yet
    # Every page uses the same generic stock photo, not a per-location image.
    drop_attributes = {"image"}
    sitemap_urls = ["https://www.rotorooter.com/sitemaps/home/sitemap.xml"]
    # The site generates one landing page per served city for SEO, most of which only
    # advertise a call-tracking phone number for the nearest branch and have no address
    # of their own. Only pages for a branch's own city include a full postal address in
    # their LocalBusiness structured data, so those without one are discarded below.
    sitemap_rules = [(r"^https://www\.rotorooter\.com/[a-z0-9]+/$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not item.get("street_address"):
            return

        apply_category(Categories.CRAFT_PLUMBER, item)
        yield item
