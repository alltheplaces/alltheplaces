from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FurnmartSpider(SitemapSpider, StructuredDataSpider):
    name = "furnmart"
    item_attributes = {"brand": "Furnmart", "brand_wikidata": "Q118185771"}

    sitemap_urls = [
        "https://www.furnmart.co.za/sitemap_stores.xml",
        "https://www.furnmart.com.na/sitemap_stores.xml",
        "https://www.furnmart.co.bw/sitemap_stores.xml",
    ]
    sitemap_rules = [("/stores/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
