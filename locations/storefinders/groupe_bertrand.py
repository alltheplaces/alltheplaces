from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature, set_closed
from locations.react_server_components import parse_rsc


class GroupeBertrandSpider(SitemapSpider):
    """
    Shared base for Groupe Bertrand's restaurant-chain sites (confirmed for Au Bureau,
    Hippopotamus, Volfoni, Le Paradis du Fruit and Léon de Bruxelles), built on their own
    "@groupe-bertrand/ui" component library over Storyblok CMS content, streamed through Next.js
    RSC flight chunks. Each store record is anchored under a stable "restaurant_myli" Storyblok
    content-type key.

    Subclasses must set `name`, `item_attributes`, `sitemap_urls` and `sitemap_rules`, and
    implement `post_process_item(item, store, raw_name)` to set `branch` from `raw_name` (the
    brand prefix format varies per site) and apply a category.
    """

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = self.extract_store(response)
        if not store:
            return

        store.update(store.pop("address", {}))
        raw_name = store.pop("name", "")
        item = DictParser.parse(store)
        item["website"] = response.url
        # supportEmail is a shared hotline, not per-location; only publicEmail (when set) is used.
        item["email"] = store.get("contact", {}).get("publicEmail") or None
        item["opening_hours"] = self.parse_hours(store.get("openings", {}))

        if store.get("status") != "open":
            set_closed(item)

        yield from self.post_process_item(item, store, raw_name)

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        raise NotImplementedError

    @staticmethod
    def extract_store(response: Response) -> dict:
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
