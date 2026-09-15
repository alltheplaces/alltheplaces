import re
from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Published in place of a branch-specific contact on many store pages.
HEAD_OFFICE_PHONE_DIGITS = "1992703010"
BRAND_FACEBOOK_PATH = "jollyesuk"


class JollyesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "jollyes_gb"
    item_attributes = {"brand": "Jollyes", "brand_wikidata": "Q45844955"}
    sitemap_urls = ["https://backend.jollyes.co.uk/media/sitemap_store.xml"]
    sitemap_rules = [(r"/store/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.split("/store/")[-1]
        item["branch"] = item.pop("name")
        item["twitter"] = None
        if re.sub(r"\D", "", item.get("phone") or "").endswith(HEAD_OFFICE_PHONE_DIGITS):
            item["phone"] = None
        if urlparse(item.get("facebook") or "").path.strip("/") == BRAND_FACEBOOK_PATH:
            item["facebook"] = None
        apply_category(Categories.SHOP_PET, item)
        yield item
