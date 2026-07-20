import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class SofiaUrbanMobilityCenterBGSpider(Spider):
    name = "sofia_urban_mobility_center_bg"
    item_attributes = {
        "brand": "Център за градска мобилност",
        "brand_wikidata": "Q7553668",
    }
    start_urls = ["https://webportal.sofiatraffic.bg/bg/contacts"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if bundle_path := response.xpath('//script[@type="module"]/@src').get():
            yield response.follow(bundle_path, callback=self.parse_bundle)

    def parse_bundle(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (anchor := re.search(r"=\{1:\{name:\{bg:", response.text)):
            return
        for office in chompjs.parse_js_object(response.text[anchor.start() + 1 :]).values():
            office.update(office.pop("location"))
            office["name"] = office["name"].get("en") or office["name"]["bg"]
            item = DictParser.parse(office)
            item["branch"] = item.pop("name")

            hours = office["workingHours"]
            item["opening_hours"] = OpeningHours()
            for day in ["Mo", "Tu", "We", "Th", "Fr"]:
                if hours.get("weekday"):
                    item["opening_hours"].add_range(day, *hours["weekday"].split("-"))
            if hours.get("saturday"):
                item["opening_hours"].add_range("Sa", *hours["saturday"].split("-"))
            if hours.get("sunday"):
                item["opening_hours"].add_range("Su", *hours["sunday"].split("-"))

            apply_category(Categories.SHOP_TICKET, item)
            yield item
