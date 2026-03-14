from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SuperdrySpider(SitemapSpider, StructuredDataSpider):
    name = "superdry"
    item_attributes = {"brand": "Superdry", "brand_wikidata": "Q1684445"}
    sitemap_urls = ["https://stores.superdry.com/sitemap.xml"]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Superdry").strip().removeprefix("™").strip()
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
