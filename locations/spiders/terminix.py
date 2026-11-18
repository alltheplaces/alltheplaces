from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TerminixSpider(SitemapSpider, StructuredDataSpider):
    name = "terminix"
    item_attributes = {"brand": "Terminix", "brand_wikidata": "Q7702831"}
    sitemap_urls = ["https://www.terminix.com/sitemap_index.xml"]
    sitemap_rules = [(r"/exterminators/\w+/[\w\-]+-(\d+)/$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data.pop("image", None)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Remove brand social links
        item.pop("facebook", None)

        apply_category(Categories.SHOP_PEST_CONTROL, item)
        yield item
