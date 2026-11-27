import json
import re
from typing import Iterable

from scrapy.http import Response
from w3lib.html import remove_tags

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

MANAGING_COUNTRIES = {
    "【管理国】中国": "CN",
    "【管理国】台湾": "TW",
    "【管理国】香港": "HK",
    "【管理国】シンガポール": "SG",
    "【管理国】ベトナム": "VN",
    "【管理国】マレーシア": "MY",
    "【管理国】オーストラリア": "AU",
}
FLAGS = {
    "テイクアウト": Extras.TAKEAWAY,
    "駐車場": Extras.PARKING,
    "クレジット(VISA等)": PaymentMethods.CREDIT_CARDS,
}


class SaizeriyaSpider(LocationCloudSpider):
    name = "saizeriya"

    item_attributes = {"brand_wikidata": "Q886564"}
    skip_auto_cc_domain = True
    api_endpoint = "https://shop.saizeriya.co.jp/sz_restaurant/api/proxy2/shop/list"
    website_formatter = "https://shop.saizeriya.co.jp/sz_restaurant/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = (
            source_feature["name"].removeprefix("サイゼリヤ ").removeprefix("Saizeriya　 ").removeprefix("Saizeriya ")
        )
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby.removeprefix("サイゼリヤ")

        apply_category(Categories.RESTAURANT, item)

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        # Overseas stores without a real location sit on the head office in Yoshikawa, Saitama
        if (item["lat"], item["lon"]) == (35.927903, 139.842093):
            item["lat"] = item["lon"] = None
            for flag in detail["flags"].values():
                for label, country in MANAGING_COUNTRIES.items():
                    if flag["value"] == "true" and flag["label"].startswith(label):
                        item["country"] = country

        texts = {}
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                texts[text["label"]] = text["value"]
            for flag in column["columns"].get("flag", []):
                if attribute := FLAGS.get(flag["label"]):
                    apply_yes_no(attribute, item, flag["value"] == "true", False)

        if phone := texts.get("電話番号"):
            item["phone"] = remove_tags(phone)

        # 24 hour times, so "10:00～2:00" closes at 2 AM
        hours = texts.get("営業時間", "").split("※")[0].strip()
        if match := re.fullmatch(r"(\d{1,2}:\d{2})[～-](\d{1,2}:\d{2})", hours):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, *match.groups())

        yield item
