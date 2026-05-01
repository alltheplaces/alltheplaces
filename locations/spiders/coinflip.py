import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoinflipSpider(CrawlSpider, StructuredDataSpider):
    name = "coinflip"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    start_urls = ["https://locations.coinflip.tech/"]

    rules = [
        Rule(LinkExtractor(allow=r"/\w+$", restrict_xpaths="//main//ul")),
        Rule(LinkExtractor(allow=r"/\w+/[a-z-]+$", restrict_xpaths="//main//ul")),
        Rule(LinkExtractor(allow=r"/\w+/[a-z-]+/[a-z-]+$", restrict_xpaths="//main//ul")),
        Rule(
            LinkExtractor(
                allow=r"/\w+/[a-z-]+/[a-z-]+/[a-z-0-9]+$",
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["AutomatedTeller"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUESTS": 1, "USER_AGENT": BROWSER_DEFAULT}

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
