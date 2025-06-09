import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaserawayUSSpider(SitemapSpider, StructuredDataSpider):
    name = "laseraway_us"
    item_attributes = {"brand_wikidata": "Q119982751", "brand": "LaserAway", "extras": Categories.SHOP_BEAUTY.value}
    sitemap_urls = ["https://www.laseraway.com/sitemap_index.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["HealthAndBeautyBusiness"]
    days = DAYS_EN
    requires_proxy = "US"  # Cloudflare captcha in use

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("LaserAway ").removeprefix("– ")
        item["lat"], item["lon"] = re.search(r"lat\":\"(-?\d+\.\d+)\",\"lng\":\"(-?\d+\.\d+)\"", response.text).groups()
        yield item
