import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RonaSpider(SitemapSpider, StructuredDataSpider):
    name = "rona"
    item_attributes = {"brand": "Rona", "brand_wikidata": "Q3415283"}
    allowed_domains = ["www.rona.ca"]
    sitemap_urls = ["https://www.rona.ca/sitemap-stores-en.xml"]
    sitemap_rules = [(r"/store/[^/]+/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["HardwareStore"]
    requires_proxy = "CA"
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if name := item.pop("name", None):
            item["branch"] = re.sub(r"\s*\bRONA\b\s*\+?\s*|^\+\s*", " ", name, flags=re.IGNORECASE).strip(" -")
        item["country"] = "CA"
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
