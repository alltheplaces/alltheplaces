import re
from typing import Iterable

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class PudostationJPSpider(GogaStoreLocatorSpider):
    name = "pudostation_jp"
    item_attributes = {"brand_wikidata": "Q86738066"}
    start_urls = ["https://map.pudo.jp/api/points"]
    website_formatter = "https://map.pudo.jp/points/{}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["postcode"] = source_feature["Zip code"]

        oh = OpeningHours()
        for field, days in [
            ("平日使用可能時間", DAYS_WEEKDAY),
            ("土曜使用可能時間", ["Sa"]),
            ("日祝使用可能時間", ["Su"]),
        ]:
            value = source_feature.get(field)
            if value == "24時間":
                oh.add_days_range(days, "00:00", "23:59")
            elif value == "なし":
                oh.set_closed(days)
            elif match := re.fullmatch(r"(\d{1,2}:\d{2}) ~ (\d{1,2}:\d{2})", value or ""):
                oh.add_days_range(days, match.group(1), match.group(2))
            else:
                # "始発～終電" (first to last train) has no fixed times
                break
        else:
            item["opening_hours"] = oh

        yield item
