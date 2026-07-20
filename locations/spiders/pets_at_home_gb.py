import json
import re
from typing import Any
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PetsAtHomeGBSpider(SitemapSpider):
    name = "pets_at_home_gb"
    item_attributes = {"brand": "Pets at Home", "brand_wikidata": "Q7179258"}
    sitemap_urls = ["https://www.petsathome.com/find-us/sitemap.xml"]
    sitemap_rules = [(r"/find-us/locations/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (match := re.search(r'JSON\.parse\(decodeURIComponent\("(.+?)"\)\)', response.text, re.DOTALL)):
            return
        document = json.loads(unquote(match.group(1)))["document"]

        item = DictParser.parse(document)
        item["branch"] = item.pop("name", "").removeprefix("Pets at Home ")
        item["website"] = response.url
        item["opening_hours"] = self.parse_opening_hours(document.get("hours"))
        apply_category(Categories.SHOP_PET, item)

        yield item

    def parse_opening_hours(self, hours: dict | None) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in (hours or {}).items():
            if not isinstance(rule, dict) or day == "holidayHours":
                continue
            if rule.get("isClosed"):
                oh.set_closed(day)
                continue
            for interval in rule.get("openIntervals", []):
                oh.add_range(day, interval["start"], interval["end"])
        return oh
