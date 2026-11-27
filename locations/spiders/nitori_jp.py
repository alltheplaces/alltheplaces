import json
import re
import unicodedata
from typing import Iterable

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

TIME_RANGE = re.compile(r"^(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})$")

FLAGS = {
    "免税": Extras.DUTY_FREE,
    "多目的トイレ": Extras.TOILETS_WHEELCHAIR,
    "授乳室": "baby_feeding=room",
    "Free Wi-Fi": Extras.WIFI,
    "ATM": Extras.ATM,
}


class NitoriJPSpider(LocationCloudSpider):
    name = "nitori_jp"
    item_attributes = {
        "brand": "ニトリ",
        "brand_wikidata": "Q10801453",
    }
    api_endpoint = "https://shop.nitori-net.jp/nitori/api/proxy2/shop/list"
    website_formatter = "https://shop.nitori-net.jp/nitori/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] == "03":
            return  # skip logistics centers

        item["branch"] = source_feature.get("name", "")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby", "")

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        texts = {}
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                texts.setdefault(text["label"], text["value"])
            for flag in column["columns"].get("flag", []):
                if tag := FLAGS.get(flag["label"]):
                    apply_yes_no(tag, item, flag["value"] == "true")

        oh = OpeningHours()
        for label, days in (("営業時間（平日）", DAYS_WEEKDAY), ("営業時間（土日祝）", DAYS_WEEKEND)):
            if match := TIME_RANGE.match(unicodedata.normalize("NFKC", texts.get(label, "")).strip()):
                oh.add_days_range(days, *match.groups())
            else:
                break  # split weekend hours or no hours at all
        else:
            item["opening_hours"] = oh

        apply_yes_no(Extras.PARKING, item, bool(re.search(r"\d台", texts.get("駐車場", ""))))

        yield item
