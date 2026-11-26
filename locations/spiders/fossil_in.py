import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.spiders.fossil import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FossilINSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "fossil_in"
    item_attributes = {"brand": "Fossil", "brand_wikidata": "Q356212"}
    sitemap_urls = ["https://www.fossil.in/sitemap-storelocator.xml"]
    sitemap_rules = [(r"^https://www\.fossil\.in/store-locator-india/", "parse")]
    wanted_types = ["Store"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["image"] = None
        match = re.fullmatch(r"store_(\d+)@fossil\.com", ld_data.get("email") or "", re.IGNORECASE)
        if not match:
            return
        item["ref"] = match.group(1)
        item["branch"] = item.pop("name").removeprefix("Fossil Exclusive Store - ")
        item["addr_full"] = item.pop("street_address")

        apply_category(Categories.SHOP_WATCHES, item)
        yield item
