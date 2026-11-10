from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BoscovsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "boscovs_us"
    item_attributes = {"brand": "Boscov's", "brand_wikidata": "Q4947190"}
    sitemap_urls = ["https://locations.boscovs.com/robots.txt"]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+\.html$", "parse_sd")]
    drop_attributes = {"facebook", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").replace("Boscov's Department Store", "").strip()
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
