from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KpmgSpider(SitemapSpider, StructuredDataSpider):
    name = "kpmg"
    item_attributes = {"brand": "KPMG", "brand_wikidata": "Q493751"}
    sitemap_urls = ["https://kpmg.com/sitemap-index.xml"]
    sitemap_rules = [(r"/offices/", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if name := item.pop("name", None):
            item["branch"] = name.removesuffix(" office").strip()
        apply_category(Categories.OFFICE_CONSULTING, item)
        yield item
