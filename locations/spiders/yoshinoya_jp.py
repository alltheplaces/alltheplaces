import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_JP, OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

FLAGS = {
    "テイクアウト": Extras.TAKEAWAY,
    "デリバリーサービス": Extras.DELIVERY,
    "駐車場": Extras.PARKING,
    "ドライブスルー": Extras.DRIVE_THROUGH,
}


class YoshinoyaJPSpider(LocationCloudSpider):
    name = "yoshinoya_jp"
    item_attributes = {"brand": "吉野家", "brand_wikidata": "Q776272"}
    api_endpoint = "https://stores.yoshinoya.com/yoshinoya/api/proxy2/shop/list"
    website_formatter = "https://stores.yoshinoya.com/yoshinoya/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] == "02":
            return  # skip offices

        item["branch"] = source_feature.get("name").removeprefix("吉野家 ")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby").removeprefix("ヨシノヤ ")
        item["phone"] = f"+81 {source_feature.get('phone')}"

        apply_category(Categories.FAST_FOOD, item)

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        oh = OpeningHours()
        for column in detail["detailColumns"]:
            for flag in column["columns"].get("flag", []):
                if flag["label"] == "Sync-閉業" and flag["value"] == "true":
                    return
                if tag := FLAGS.get(flag["label"]):
                    apply_yes_no(tag, item, flag["value"] == "true", False)
            if column.get("name") != "通常営業時間":
                continue
            for text in column["columns"].get("text", []):
                # e.g. "通常営業時間 - 月": "5:00 - 2:00", or "0:00 - 2:00, 5:00 - 2:00" when the night before runs past midnight
                if not (day := sanitise_day(text["label"][-1], DAYS_JP)):
                    continue
                if text["value"] == "休業日":
                    oh.set_closed(day)
                elif text["value"] in ("24h", "0:00 - 0:00"):
                    oh.add_range(day, "00:00", "23:59")
                else:
                    ranges = text["value"].split(", ")
                    for times in ranges:
                        if len(ranges) > 1 and times.startswith("0:00 - "):
                            continue
                        oh.add_range(day, *times.split(" - "))
        item["opening_hours"] = oh

        if any(category["code"] == "0101004" for category in source_feature["categories"]):
            item["extras"]["takeaway"] = "only"
            item["extras"]["delivery"] = "only"

        yield item
