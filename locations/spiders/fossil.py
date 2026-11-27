import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FossilSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "fossil"
    item_attributes = {"brand": "Fossil", "brand_wikidata": "Q356212"}
    sitemap_urls = ["https://stores.fossil.com/sitemap.xml"]
    sitemap_rules = [(r"^https://stores\.fossil\.com/(?!in/)[a-z]{2}/(?:[^/]+/)+[^/]+-\d+/?$", "parse")]
    wanted_types = ["Store"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = item["image"] = None
        item["ref"] = response.url.rstrip("/").rsplit("-", 1)[-1]
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := json.loads(ld).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo["latitude"]
                item["lon"] = geo["longitude"]

        apply_category(Categories.SHOP_WATCHES, item)
        yield item
