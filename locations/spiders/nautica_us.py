import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The Yext store pages mark their content up as schema.org microdata rather
# than JSON-LD, which the structured data spider converts before parsing.
#
# The sitemap also lists the state and city directory pages, so only the URLs
# with a third path segment are followed.
#
# The Puerto Rico stores leave addressRegion empty, so the region is taken from
# the URL, and they are labelled with their own country code.

US_TERRITORIES = {"AS", "GU", "MP", "PR", "UM", "VI"}


class NauticaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "nautica_us"
    item_attributes = {"brand": "Nautica", "brand_wikidata": "Q6981479"}
    allowed_domains = ["stores.nautica.com"]
    sitemap_urls = ["https://stores.nautica.com/sitemap.xml"]
    sitemap_rules = [(r"^https://stores\.nautica\.com/[a-z]{2}/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["ClothingStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # The microdata itemid is "https://stores.nautica.com/#52238092".
        if store_id := re.search(r"#(\d+)$", item.get("ref") or ""):
            item["ref"] = store_id.group(1)
        # Every store is named just "Nautica", so there is no branch name.
        item["name"] = None
        item["branch"] = None
        # The image is the brand's logo.
        item["image"] = None

        region = response.url.strip("/").split("/")[-3].upper()
        if not item.get("state"):
            item["state"] = region
        if region in US_TERRITORIES:
            item["country"] = region

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
