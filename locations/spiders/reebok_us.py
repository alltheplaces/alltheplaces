from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ReebokUSSpider(SitemapSpider, StructuredDataSpider):
    name = "reebok_us"
    item_attributes = {"brand": "Reebok"}
    sitemap_urls = ["https://stores.reebok.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = response.xpath("normalize-space(//h1)").get()
        item["image"] = None
        if response.url.endswith("/25-dry-dock-ave"):
            # Reebok corporate HQ, listed in the store finder but not a retail store
            apply_category(Categories.OFFICE_COMPANY, item)
        else:
            item["brand_wikidata"] = "Q466183"
            apply_yes_no("factory_outlet", item, True)
            apply_category(Categories.SHOP_CLOTHES, item)
        yield item
