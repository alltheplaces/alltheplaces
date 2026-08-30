from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WeFixFRBESpider(SitemapSpider, StructuredDataSpider):
    name = "wefix_fr_be"
    item_attributes = {"brand": "WeFix", "brand_wikidata": "Q121543865"}
    sitemap_urls = ["https://boutique.wefix.net/locationsitemap1.xml"]
    sitemap_rules = [(r"https\:\/\/boutique\.wefix\.net\/.+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        if item.get("phone") == "+33 1 76 50 76 50":
            item.pop("phone", None)

        yield item
