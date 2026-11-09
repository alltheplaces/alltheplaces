from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SafewayCASpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "safeway_ca"
    item_attributes = {"brand": "Safeway", "brand_wikidata": "Q17111901"}
    sitemap_urls = ["https://www.safeway.ca/sitemap/stores/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse")]
    wanted_types = ["GroceryStore"]
    search_for_twitter = False
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("/", 1)[-1]
        item["branch"] = item.pop("name").removeprefix("Safeway").strip()
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
