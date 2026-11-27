import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class MatsuyaJPSpider(LocationCloudSpider):
    name = "matsuya_jp"
    api_endpoint = "https://pkg.navitime.co.jp/matsuyafoods/api/proxy2/shop/list"
    website_formatter = "https://pkg.navitime.co.jp/matsuyafoods/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        if "併設" in source_feature.get("name"):  # removes locations with multiple brands
            return

        match source_feature["categories"][0]["code"]:
            case "0101":
                item["branch"] = source_feature.get("name").removeprefix("松屋 ")
                item["extras"]["branch:ja-Hira"] = source_feature.get("ruby").removeprefix("まつや ")
                item.update({"brand_wikidata": "Q848773"})
                apply_category(Categories.FAST_FOOD, item)
            case _:
                item["branch"] = source_feature.get("name")
                item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
                item["brand"] = item["name"] = source_feature["categories"][0]["name"]
                apply_category(Categories.RESTAURANT, item)

        item["phone"] = source_feature.get("phone")

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        hours = next(
            t["value"]
            for c in detail["detailColumns"]
            for t in c.get("columns", {}).get("text", [])
            if t["label"] == "営業時間"
        )
        # Day-specific schedules are free text and are left unparsed
        hours = re.split(r"[、（]ラストオーダー", hours)[0].strip()
        item["opening_hours"] = OpeningHours()
        if hours == "24時間営業":
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        elif m := re.fullmatch(r"(\d+)時(?:(\d+)分)?から翌?(\d+)時(?:(\d+)分)?", hours):
            item["opening_hours"].add_days_range(DAYS, f"{m[1]}:{m[2] or '00'}", f"{m[3]}:{m[4] or '00'}")

        flags = {flag["label"]: flag["value"] == "true" for flag in detail["flags"].values()}
        apply_yes_no(Extras.DELIVERY, item, flags["松弁デリバリー"])
        apply_yes_no(Extras.PARKING, item, flags["駐車場あり"])
        apply_yes_no(Extras.WHEELCHAIR, item, flags["バリアフリー"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, flags["ドライブスルー"])
        apply_yes_no(Extras.SELF_SERVICE, item, flags["セルフサービス"])

        yield item
