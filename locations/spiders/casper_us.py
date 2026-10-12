from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CasperUSSpider(SitemapSpider, StructuredDataSpider):
    name = "casper_us"
    item_attributes = {"brand": "Casper", "brand_wikidata": "Q20539294"}
    sitemap_urls = ["https://stores.casper.com/sitemap.xml"]
    sitemap_rules = [(r"stores\.casper\.com\/[^/]+/[^/]+/.*html$", "parse_sd")]
    drop_attributes = {"image"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BED, item)
        yield item
