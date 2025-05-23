from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class TeremokRUSpider(scrapy.Spider):
    name = "teremok_ru"
    allowed_domains = ["teremok.ru"]
    item_attributes = {"brand": "Теремок", "brand_wikidata": "Q4455593"}
    start_urls = ["https://teremok.ru/api/main/place/list"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DOWNLOAD_TIMEOUT": 300,
        "RETRY_TIMES": 10,  # Sometimes connection refused by server, increased retry might help
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json():
            poi.pop("city")  # skip city id, address contains the city name
            item = DictParser.parse(poi)
            item["lat"], item["lon"] = poi.get("map", [None, None])
            item["website"] = urljoin(self.start_urls[0], poi.get("url"))
            self.parse_hours(poi, item)
            yield item

    def parse_hours(self, poi: dict, item: Feature) -> Any:
        if hours := poi.get("mode"):
            ranges = []
            for period in hours:
                days = period.get("days")
                time = period.get("time")
                ranges.append(f"{days}: {time}")
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string("; ".join(ranges), DAYS_RU, NAMED_DAY_RANGES_RU)
                item["opening_hours"] = oh
            except Exception:
                self.logger.warning(f"Parse hours failed: {hours}")
                self.crawler.stats.inc_value("atp/hours/failed")
