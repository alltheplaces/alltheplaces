import json
from typing import Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SmashburgerSpider(CrawlSpider, StructuredDataSpider):
    name = "smashburger"
    item_attributes = {"brand": "Smashburger", "brand_wikidata": "Q17061332"}
    allowed_domains = ["smashburger.com"]
    start_urls = ["https://smashburger.com/locations"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://smashburger\.com/locations/\w\w(?:/\w\w)?(?:/[^/]+)?$")),
        Rule(LinkExtractor(allow=r"^https://smashburger\.com/locations/\w\w/\w\w/[^/]+/[^/]+$"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url
        item.pop("facebook")
        item.pop("twitter")

        page_props = response.xpath('//script[contains(text(), "decodeURIComponent")]/text()').re_first(
            r'JSON\.parse\(decodeURIComponent\("([^"]+)"\)'
        )
        if page_props:
            document = json.loads(unquote(page_props))["document"]
            item["phone"] = document.get("mainPhone")
            hours = document.get("hours", {})
            item["opening_hours"] = oh = OpeningHours()
            for day in DAYS_FULL:
                day_hours = hours.get(day.lower(), {})
                if day_hours.get("isClosed"):
                    oh.set_closed(day)
                for interval in day_hours.get("openIntervals", []):
                    oh.add_range(day, interval["start"], interval["end"])

        apply_category(Categories.FAST_FOOD, item)
        yield item
