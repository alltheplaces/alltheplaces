from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import set_closed
from locations.react_server_components import parse_rsc


class AubureauFRSpider(SitemapSpider):
    name = "aubureau_fr"
    item_attributes = {"brand": "Au Bureau", "brand_wikidata": "Q100701566", "name": "Au Bureau"}
    sitemap_urls = ["https://www.aubureau.fr/sitemap.xml"]
    sitemap_rules = [(r"/restaurant-brasserie/au-bureau-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = self.extract_store(response)
        if not store:
            return

        branch = store.pop("name", "").removeprefix("Au Bureau - ")
        store.update(store.pop("address", {}))

        item = DictParser.parse(store)
        item["branch"] = branch
        item["website"] = response.url
        item["email"] = store.get("contact", {}).get("publicEmail")
        item["opening_hours"] = self.parse_hours(store.get("openings", {}))

        if store.get("status") != "open":
            set_closed(item)

        apply_category(Categories.RESTAURANT, item)
        yield item

    @staticmethod
    def extract_store(response: Response) -> dict:
        # The store record is embedded (quote-escaped) inside Next.js RSC flight chunks, under a
        # "restaurant_myli" key - stable across pages, unlike the numeric row IDs around it.
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join(s for _, s in objs).encode()
        return DictParser.get_nested_key(dict(parse_rsc(rsc)), "restaurant_myli") or {}

    def parse_hours(self, openings: dict) -> OpeningHours:
        oh = OpeningHours()
        try:
            for day in openings.get("businessOpenings", []):
                for timetable in day["timetables"]:
                    oh.add_range(DAYS[day["dayOfWeek"] - 1], timetable["open"], timetable["close"])
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {e}")
        return oh
