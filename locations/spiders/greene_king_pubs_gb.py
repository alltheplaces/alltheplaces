from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GreeneKingPubsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "greene_king_pubs_gb"
    item_attributes = {
        "brand": "Greene King",
        "brand_wikidata": "Q5564162",
    }
    sitemap_urls = ["https://www.greeneking.co.uk/sitemap.xml"]
    sitemap_rules = [(r"\/pubs\/([-\w]+)\/([-\w]+)\/?$", "parse_sd")]
    custom_settings = {"REDIRECT_ENABLED": False, "USER_AGENT": BROWSER_DEFAULT,"DOWNLOAD_TIMEOUT":60}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.PUB, item)
        yield item
