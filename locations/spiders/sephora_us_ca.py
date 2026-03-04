from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours, sanitise_day
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SephoraUSCASpider(SitemapSpider):
    name = "sephora_us_ca"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    sitemap_urls = [
        "https://www.sephora.com/sephora-store-sitemap.xml",
        "https://www.sephora.com/sephora-store-sitemap_en-CA.xml",
    ]
    sitemap_rules = [
        (r"\/happening\/stores\/(?!kohls).+", "parse"),
        (r"\/ca\/en\/happening\/stores\/(?!kohls).+", "parse"),
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = None
        for script in response.xpath('//script[contains(text(), "storeId")]/text()').getall():
            try:
                candidate = DictParser.get_nested_key(chompjs.parse_js_object(script), "store")
                if isinstance(candidate, dict) and "storeId" in candidate:
                    store = candidate
                    break
            except Exception:
                continue
        if not store:
            return

        if store.get("storeType") != "SEPHORA":
            self.crawler.stats.inc_value("atp/items/skipped")
            return

        item = DictParser.parse(store)
        item["ref"] = store.get("storeId")
        item["branch"] = item.pop("name").title().removeprefix("Sephora ")
        item["website"] = response.url

        self._parse_hours(item, store.get("storeHours", {}))

        apply_category(Categories.SHOP_COSMETICS, item)
        yield item

    @staticmethod
    def _parse_hours(item: Feature, hours: dict) -> None:
        oh = OpeningHours()
        for day_name in DAYS_FULL:
            value = hours.get(f"{day_name.lower()}Hours")
            if not value:
                continue
            try:
                open_time, close_time = value.split("-")
                oh.add_range(sanitise_day(day_name), open_time.strip(), close_time.strip(), "%I:%M%p")
            except (ValueError, AttributeError):
                continue
        item["opening_hours"] = oh
