from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TommyBahamaSpider(SitemapSpider, StructuredDataSpider):
    name = "tommy_bahama"
    item_attributes = {"brand": "Tommy Bahama", "brand_wikidata": "Q3531299"}
    sitemap_urls = ["https://www.tommybahama.com/en/sitemap.xml"]
    sitemap_rules = [("/en/store/", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"] = response.url
        yield item
