import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
from locations.structured_data_spider import StructuredDataSpider


class LaserawayUSSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "laseraway_us"
    item_attributes = {"brand_wikidata": "Q119982751", "brand": "LaserAway"}
    sitemap_urls = ["https://www.laseraway.com/custom_location-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["HealthAndBeautyBusiness"]
    days = DAYS_EN
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//table[@id="sitemap"]'
    # Allow "other" resource types which includes XSL stylesheets. Firefox
    # returns an exception if a XSL stylesheet cannot be loaded.
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: not (
            request.resource_type in ["document", "script", "xhr", "fetch", "image", "other"]
        )
    }
    handle_httpstatus_list = [403]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("LaserAway ").removeprefix("– ")
        item["lat"], item["lon"] = re.search(r"lat\":\"(-?\d+\.\d+)\",\"lng\":\"(-?\d+\.\d+)\"", response.text).groups()
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
