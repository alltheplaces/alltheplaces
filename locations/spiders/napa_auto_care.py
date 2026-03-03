import re
import urllib
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class NapaAutoCareSpider(SitemapSpider):
    name = "napa_auto_care"
    item_attributes = {"brand": "NAPA AutoCare Center", "brand_wikidata": "Q6970842"}
    sitemap_urls = ["https://www.napaonline.com/autocare_sitemap.xml"]
    sitemap_rules = [(r"/en/autocare/\?facilityId=", "parse")]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if match := re.search(r"https://maps\.googleapis\.com/maps/api/staticmap\?center=(.+?)\"", response.text):
            location_info = urllib.parse.unquote(match.group(1))
            item = Feature()
            item["ref"] = response.url.split("facilityId=")[1].strip("/")
            item["website"] = response.url
            item["addr_full"] = clean_address(location_info.split("Phone:")[0]).replace("+", " ")
            if phone := re.search(r"phoneNumber=\"(.+?)\"/>", location_info):
                item["phone"] = phone.group(1)
            if coordinates := re.search(r"\|label:\d\|(-?\d+\.\d+),(-?\d+\.\d+)&", location_info):
                item["lat"], item["lon"] = coordinates.groups()
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
