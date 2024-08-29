from html import unescape
from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LaserawayUSSpider(WPStoreLocatorSpider):
    name = "laseraway_us"
    item_attributes = {"brand_wikidata": "Q119982751", "brand": "LaserAway", "extras": Categories.SHOP_BEAUTY.value}
    allowed_domains = [
        "www.laseraway.com",
    ]
    days = DAYS_EN
    requires_proxy = "US"  # Cloudflare captcha in use

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item["branch"] = unescape(item.pop("name").removeprefix("LaserAway ")).removeprefix("– ")
        item["website"] = urljoin("https://www.laseraway.com", feature["url"])
        yield item
