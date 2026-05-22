import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RogersCASpider(SitemapSpider, StructuredDataSpider):
    name = "rogers_ca"
    item_attributes = {"brand": "Rogers", "brand_wikidata": "Q3439663"}
    allowed_domains = ["rogers.com"]
    sitemap_urls = ["https://www.rogers.com/stores/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.rogers\.com/stores/[^/]+/[^/]+$$", "parse")]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["image"] = None
        if "Available in the Fido" in item["name"]:
            item["located_in"] = "Fido"
            item["name"] = None

        if m := re.search(r"Rogers Store at\s+(.*?)\s*-\s", response.xpath("//title/text()").get() or ""):
            if branch := m.group(1).strip():
                item["branch"] = branch

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
