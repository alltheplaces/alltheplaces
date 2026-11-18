import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LapperreBESpider(SitemapSpider):
    name = "lapperre_be"
    item_attributes = {"brand": "Lapperre", "brand_wikidata": "Q126195805"}
    sitemap_urls = ["https://shops.lapperre.be/sitemap.xml"]
    sitemap_rules = [
        (r"https://www\.lapperre\.be/nl/hoorcentrum/.+/.+/.+", "parse"),
    ]

    def parse(self, response, **kwargs):
        script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not script:
            return
        data = json.loads(script)
        store = self._find_store(data)
        if not store:
            return

        store["location"] = self._find_coordinate(data, store.get("id"))
        item = DictParser.parse(store)
        branch = re.sub(r"^(?:World of Hearing )?Lapp+erre (?:hoorcentrum )?", "", item.pop("name"))
        if " bij " in branch:
            branch, item["located_in"] = branch.split(" bij ", 1)
        item["branch"] = branch
        email = (store.get("emails") or [None])[0]
        item["email"] = None if email == "contact@lapperre.be" else email
        item["street_address"] = store.get("addressLine1")
        item["website"] = response.url
        item["opening_hours"] = self.parse_hours(store.get("hours"))

        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item

    @staticmethod
    def parse_hours(hours: list | None) -> OpeningHours | None:
        if not hours:
            return None
        oh = OpeningHours()
        try:
            for day_hours in hours:
                if day_hours.get("isClosed"):
                    continue
                for interval in day_hours.get("openIntervals") or []:
                    oh.add_range(day_hours.get("day"), interval["start"], interval["end"])
        except (KeyError, TypeError):
            return None
        return oh

    @staticmethod
    def _find_store(data: dict) -> dict | None:
        components = data.get("props", {}).get("pageProps", {}).get("data", {}).get("components", [])
        for component in components:
            for slide in component.get("slides") or []:
                store = (slide.get("storeConfig") or {}).get("storeData")
                if store:
                    return store
        return None

    @staticmethod
    def _find_coordinate(data: dict, store_id: str | None) -> dict | None:
        components = data.get("props", {}).get("pageProps", {}).get("data", {}).get("components", [])
        for component in components:
            active = component.get("activeElement") or {}
            if active.get("id") == store_id:
                return active.get("coordinate")
        return None
