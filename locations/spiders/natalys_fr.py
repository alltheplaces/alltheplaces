from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class NatalysFRSpider(SitemapSpider, StructuredDataSpider):
    name = "natalys_fr"
    item_attributes = {"brand": "Natalys", "brand_wikidata": "Q3336439"}
    sitemap_urls = ["https://www.natalys.com/robots.txt"]
    sitemap_rules = [
        ("/nos-boutiques/", "parse_sd"),
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        extract_google_position(item, response)
        apply_category(Categories.SHOP_BABY_GOODS, item)
        yield item
