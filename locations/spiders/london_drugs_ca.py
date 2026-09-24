import json
import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class LondonDrugsCASpider(SitemapSpider, PlaywrightSpider):
    name = "london_drugs_ca"
    item_attributes = {"brand": "London Drugs", "brand_wikidata": "Q3258955"}
    allowed_domains = ["www.londondrugs.com"]
    sitemap_urls = ["https://www.londondrugs.com/stores/sitemap.xml"]
    sitemap_rules = [("https://www.londondrugs.com/stores/[^/]+/[^/]+/[^/]+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response):
        json_data = json.loads(
            re.search(
                r"({.+})[0-9a-z]+:\[", response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", "")
            ).group(1)
        )
        item = DictParser.parse(json_data)
        item["branch"] = item.pop("name")
        item["ref"] = item["website"] = response.url
        oh = OpeningHours()
        for day_time in json_data.get("openingHoursSpecification"):
            day = day_time.get("dayOfWeek")[0]
            open_time = day_time.get("opens")
            close_time = day_time.get("closes")
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
