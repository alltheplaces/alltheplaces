from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SaveFRSpider(SitemapSpider, StructuredDataSpider):
    name = "save_fr"
    item_attributes = {"brand": "Save", "brand_wikidata": "Q121289450"}
    sitemap_urls = ["https://magasin.save.co/sitemap.xml"]
    sitemap_rules = [(r"https://magasin\.save\.co/.+\d+/?$", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
