import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CoinflipSpider(SitemapSpider, StructuredDataSpider):
    name = "coinflip"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    sitemap_urls = ["https://coinflip.tech/locations-sitemap.xml"]
    sitemap_rules = [(r"https://locations.coinflip.tech/[^/]+/[^/]+/[^/]+/[a-z0-9]+", "parse_sd")]
    wanted_types = ["AutomatedTeller"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_DELAY": 3, "CONCURRENT_REQUESTS": 1}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", ld_data["hasMap"]).groups()
        oh = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            day = DAYS_FULL[int(day_time["dayOfWeek"][0])]
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p")
        item["opening_hours"] = oh
        yield item
