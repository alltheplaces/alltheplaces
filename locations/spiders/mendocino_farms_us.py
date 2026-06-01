from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.react_server_components import parse_rsc


class MendocinoFarmsUSSpider(Spider):
    name = "mendocino_farms_us"
    item_attributes = {"brand": "Mendocino Farms", "brand_wikidata": "Q110671982"}
    start_urls = ["https://www.mendocinofarms.com/location-directory/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for sublist in DictParser.iter_matching_keys(data, "items"):
            for store in sublist:
                if not store.get("status", {}).get("available"):
                    continue
                if "coming_soon" in (store.get("data") or {}).get("attributes", []):
                    continue

                item = DictParser.parse(store)
                item["ref"] = str(store["id"])
                item["branch"] = item.pop("name", None)
                item["street_address"] = item.pop("street", None)
                item["lat"] = store["address"].get("latitude")
                item["lon"] = store["address"].get("longitude")
                if slug := store.get("slug"):
                    item["website"] = f"https://www.mendocinofarms.com/location-directory/{slug}/"

                item["opening_hours"] = OpeningHours()
                for day, slot in (store.get("hours") or {}).get("business", {}).items():
                    if (day_code := sanitise_day(day)) and slot.get("start") and slot.get("end"):
                        item["opening_hours"].add_range(
                            day_code, slot["start"].split(" ", 1)[1][:5], slot["end"].split(" ", 1)[1][:5]
                        )

                additionals = store.get("additionals") or []
                apply_yes_no(Extras.WIFI, item, "wi_fi" in additionals)
                apply_yes_no(Extras.WHEELCHAIR, item, "has_wheelchair_accessible_entrance" in additionals)
                apply_yes_no(Extras.TOILETS, item, "has_restroom" in additionals)
                apply_yes_no(Extras.INDOOR_SEATING, item, "has_seating" in additionals)
                apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "has_wheelchair_accessible_restroom" in additionals)

                apply_category(Categories.RESTAURANT, item)
                yield item
