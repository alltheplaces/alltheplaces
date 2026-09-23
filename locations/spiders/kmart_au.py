from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KmartAUSpider(SitemapSpider, StructuredDataSpider):
    name = "kmart_au"
    item_attributes = {"brand": "Kmart", "brand_wikidata": "Q6421682", "country": "AU"}
    allowed_domains = ["kmart.com.au"]
    sitemap_urls = ["https://www.kmart.com.au/sitemap/au/storelocation-sitemap.xml"]
    sitemap_rules = [("/store-detail/", "parse_sd")]
    drop_attributes = {"facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        name = item.get("name") or ""
        item["branch"] = name.removeprefix("Kmart ").replace("K Hub", "").strip()
        if "K Hub" in name:
            item["name"] = "K Hub"
        else:
            item["name"] = "Kmart"
        extract_google_position(item, response)
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
