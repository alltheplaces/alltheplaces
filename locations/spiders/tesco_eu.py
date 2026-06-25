from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tesco_gb import TescoGBSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TescoEUSpider(SitemapSpider, StructuredDataSpider):
    name = "tesco_eu"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sitemap_urls = [
        "https://www.itesco.cz/prodejny/sitemap.xml",
        "https://www.tesco.hu/aruhazak/sitemap.xml",
        "https://www.tesco.sk/obchody/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/(prodejny|aruhazak)/[^/]+/[^/]+/?$", "parse_sd"),
        (r"/obchody/[^/]+/[^/]+/[^/]+/?$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Extra" in item["name"].title():
            apply_category(Categories.SHOP_SUPERMARKET, item)
            item.update(TescoGBSpider.TESCO_EXTRA)
        elif "Expres" in item["name"].title():
            apply_category(Categories.SHOP_CONVENIENCE, item)
            item.update(TescoGBSpider.TESCO_EXPRESS)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)
            item.update(TescoGBSpider.TESCO)
        yield item
