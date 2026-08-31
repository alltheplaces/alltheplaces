import json
import re
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HippopotamusFRSpider(SitemapSpider):
    name = "hippopotamus_fr"
    item_attributes = {"brand": "Hippopotamus", "brand_wikidata": "Q3136174"}
    sitemap_urls = ["https://www.hippopotamus.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/hippopotamus-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = self.extract_store(response.text)
        if not store:
            return
        branch = store.pop("name").removeprefix("Hippopotamus ")
        contact = store.get("contact")
        store.update(store.pop("address"))
        item = DictParser.parse(store)
        item["branch"] = branch
        if isinstance(contact, dict):
            item["email"] = contact.get("publicEmail")
        item["website"] = response.url
        item["opening_hours"] = self.parse_hours(store.get("openings", {}))
        apply_category(Categories.RESTAURANT, item)
        yield item

    @staticmethod
    def extract_store(html: str) -> dict:
        # The store object is embedded (quote-escaped) inside a Next.js RSC flight chunk.
        for chunk in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html):
            flight = json.loads(chunk)
            if (start := flight.find('{"id":"loc_')) != -1:
                return chompjs.parse_js_object(flight[start:])
        return {}

    def parse_hours(self, openings: dict) -> OpeningHours:
        oh = OpeningHours()
        try:
            for day in openings.get("businessOpenings", []):
                for timetable in day["timetables"]:
                    oh.add_range(DAYS[day["dayOfWeek"] - 1], timetable["open"], timetable["close"])
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {e}")
        return oh
