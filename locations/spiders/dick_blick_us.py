from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class DickBlickUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dick_blick_us"
    item_attributes = {"brand": "Dick Blick", "brand_wikidata": "Q5272692"}
    allowed_domains = ["www.dickblick.com"]
    sitemap_urls = ["https://www.dickblick.com/robots.txt"]
    sitemap_rules = [(r"/stores/[-\w]+/[-\w]+/$", "parse_sd")]
    time_format = "%I:%M%p"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    search_for_twitter = False
    search_for_facebook = False

    def _get_sitemap_body(self, response: Response) -> bytes:
        if "/v2/sitemap/" in response.url:
            return response.body
        return super()._get_sitemap_body(response)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if "CLOSED" in item["name"]:
            set_closed(item)
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CRAFT, item)
        yield item
