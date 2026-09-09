import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

DAYS_BY_NUMBER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class YvesDelormeSpider(JSONBlobSpider):
    name = "yves_delorme"
    item_attributes = {"brand": "Yves Delorme", "brand_wikidata": "Q131196262", "name": "Yves Delorme"}
    start_urls = ["https://france.yvesdelorme.com/plugincompany_storelocator/storelocation/storesjson/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_feature_array(self, response: TextResponse, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            # The store finder also includes independently owned, multi-brand
            # boutiques (e.g. "La Plume Lavée", "Boutique Desforges", "Laurence
            # Tavernier") which stock Yves Delorme products but do not trade
            # under the Yves Delorme brand. Only keep locations actually named
            # after the brand.
            if not re.search(r"yves\s*delorme", feature.get("locname", ""), re.IGNORECASE):
                continue
            if feature.get("lat") == "0" and feature.get("lng") == "0":
                # Broken placeholder record with swapped city/postal fields and
                # no coordinates, duplicating another store with correct data
                # (e.g. storelocation_id 3469 duplicates 3476, both "Lausanne").
                continue
            yield from super().parse_feature_array(response, [feature])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["storelocation_id"]
        name = re.sub(r"(?i)^\s*(boutique\s+)?yves\s*delorme\s*", "", item.pop("name"))
        item["branch"] = name.strip(" -")
        item["website"] = feature.get("pageurl")

        oh = OpeningHours()
        for day_number, day in enumerate(DAYS_BY_NUMBER, start=1):
            # Usually two open/close pairs per day (morning/afternoon either
            # side of a lunch break), but when a store has no lunch break the
            # source leaves the middle two fields blank and only populates the
            # first "beg" and last "end" field, e.g. beg, None, None, end for
            # a single continuous 10:00-19:00 span. Filtering out the blanks
            # and pairing what's left handles both shapes.
            times = [
                feature.get(f"schedule_d{day_number}_{period}_{part}")
                for period in ("p1", "p2")
                for part in ("beg", "end")
            ]
            times = [t for t in times if t]
            for open_time, close_time in zip(times[::2], times[1::2]):
                oh.add_range(day, open_time, close_time, time_format="%H:%M")
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_HOUSEHOLD_LINEN, item)

        yield item
