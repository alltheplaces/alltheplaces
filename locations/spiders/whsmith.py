import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class WhsmithSpider(SitemapSpider):
    name = "whsmith"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712"}
    allowed_domains = ["whsmith.co.uk"]
    sitemap_urls = ["https://www.whsmith.co.uk/SiteMap/sitemap-pages.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse")]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
    }
    coordinates_pattern = re.compile(r"google\.maps\.LatLng\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//*[@class="shop-styling__address"]/p/text()').getall())
        if coordinates := re.search(self.coordinates_pattern, response.text):
            item["lat"], item["lon"] = coordinates.groups()

        apply_category(Categories.SHOP_NEWSAGENT, item)

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//li[@class="whs-hours-item"]'):
            day = rule.xpath('.//*[contains(@class, "day")]/text()').get("")
            hours = rule.xpath('.//*[contains(@class, "time")]/text()').get("").replace("24hr-24hr", "00:00-23:59")
            item["opening_hours"].add_ranges_from_string(f"{day} {hours}")
        yield item
