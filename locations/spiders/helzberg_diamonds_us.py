from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HelzbergDiamondsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "helzberg_diamonds_us"
    item_attributes = {"brand": "Helzberg Diamonds", "brand_wikidata": "Q16995161"}
    sitemap_urls = ["https://www.helzberg.com/sitemap_stores-custom.xml"]
    sitemap_rules = [(r"/stores/[a-z]{2}/[^/]+/[^/]+-\d+$", "parse_sd")]
    wanted_types = ["JewelryStore"]
    time_format = "%I:%M%p"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name")
        item["website"] = response.url
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
