from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EnjoyTacosSpider(SitemapSpider, StructuredDataSpider):
    name = "enjoy_tacos"
    item_attributes = {"brand": "Enjoy Tacos", "brand_wikidata": "Q141242529"}
    sitemap_urls = ["https://enjoytacos.belorder.com/sitemap.xml"]
    sitemap_rules = [(r"https\:\/\/enjoytacos\.belorder\.com\/\/restaurants\/.+$", "parse_sd")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
