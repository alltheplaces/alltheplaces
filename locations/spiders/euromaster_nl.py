from collections.abc import AsyncIterator
from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class EuromasterNLSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "euromaster_nl"
    item_attributes = {"brand": "Euromaster", "brand_wikidata": "Q3060668"}
    sitemap_urls = ["https://www.euromaster.nl/sitemap.xml"]
    sitemap_follow = ["fitters"]
    sitemap_rules = [(r"^https://www\.euromaster\.nl/garages/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    # AWS WAF answers plain requests with a 202 JS challenge.
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type != "document"
        and ".awswaf.com/" not in request.url,
        "ROBOTSTXT_OBEY": False,
    }

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://www.euromaster.nl/garages",
            callback=self.parse_warmup,
            meta={"playwright_page_methods": [PageMethod("wait_for_selector", "footer")]},
        )

    async def parse_warmup(self, response: Response) -> AsyncIterator[Any]:
        async for request in super().start():
            yield request

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Euromaster ")
        item["website"] = response.url
        # JSON-LD dayOfWeek values are garbled ("????day-2????"); parse from HTML table instead.
        oh = OpeningHours()
        days = response.xpath('//*[@class="tableHoraires"]//tr/th/text()').getall()
        hours = response.xpath('//*[@class="tableHoraires"]//tr/td/text()').getall()
        for day, hour in zip(days, hours):
            oh.add_ranges_from_string(ranges_string=day + " " + hour, days=DAYS_NL, delimiters=[" - "])
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
