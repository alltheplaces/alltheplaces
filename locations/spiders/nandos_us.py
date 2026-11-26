from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class NandosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "nandos_us"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.nandosperiperi.com/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[^/?#]+/?$", "parse")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["ref"].split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Nando's Peri Peri ")
        apply_category(Categories.RESTAURANT, item)

        yield item
