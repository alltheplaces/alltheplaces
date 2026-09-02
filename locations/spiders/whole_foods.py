import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WholeFoodsSpider(SitemapSpider):
    name = "whole_foods"
    item_attributes = {"brand": "Whole Foods Market", "brand_wikidata": "Q1809448"}
    allowed_domains = ["wholefoodsmarket.com"]
    sitemap_urls = ["https://www.wholefoodsmarket.com/robots.txt"]
    sitemap_rules = [(r"/stores/([^/]+)$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath('//script[contains(@data-a-state, "detail-page-state")]/text()').get()
        if not script:
            return
        location = json.loads(script)["location"]
        geocode = location.get("geocode") or {}
        location["latitude"], location["longitude"] = geocode.get("latitude"), geocode.get("longitude")

        item = DictParser.parse(location)
        item["ref"] = location.get("storeCode")
        item["branch"] = item.pop("name", None)
        item["street_address"] = ", ".join((location.get("address") or {}).get("addressLines") or [])
        item["website"] = response.url
        item["opening_hours"] = self.parse_hours(location)

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    def parse_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        timezone = (location.get("locationFacets") or [{}])[0].get("timeZone")
        if not timezone:
            return oh
        tz = ZoneInfo(timezone)
        for day in location.get("operationalDailyHours") or []:
            for period in day.get("operatingHours") or []:
                start = datetime.fromisoformat(period["startTime"].replace("Z", "+00:00")).astimezone(tz)
                end = datetime.fromisoformat(period["endTime"].replace("Z", "+00:00")).astimezone(tz)
                oh.add_range(DAYS[start.weekday()], start.strftime("%H:%M"), end.strftime("%H:%M"))
        return oh
