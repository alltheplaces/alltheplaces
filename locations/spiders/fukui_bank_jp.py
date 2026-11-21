import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class FukuiBankJPSpider(LocationCloudSpider):
    name = "fukui_bank_jp"
    item_attributes = {
        "brand": "福井銀行",
        "brand_wikidata": "Q11591768",
        "extras": {"brand:en": "Fukui Bank", "brand:ja": "福井銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/fukuibank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/fukuibank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case "03":
                # インターネット支店 (internet branch) — virtual, skip
                return
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        # Phone is embedded as an HTML tel: link in address_name
        if addr_html := source_feature.get("address_name", ""):
            if phone_match := re.search(r'href="tel:([^"]+)"', addr_html):
                item["phone"] = phone_match.group(1)

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        counter_hours = OpeningHours()
        atm_hours = OpeningHours()
        for column in detail["detailColumns"]:
            for flag in column["columns"].get("flag", []):
                if flag["label"] == "バリアフリー対応店舗":
                    apply_yes_no(Extras.WHEELCHAIR, item, flag["value"] == "true")
            for text in column["columns"].get("text", []):
                if text["label"] == "窓口営業時間":
                    self.parse_hours(counter_hours, text["value"])
                elif text["label"] == "ATM営業時間":
                    self.parse_hours(atm_hours, text["value"])

        if source_feature["categories"][0]["code"] == "02":
            item["opening_hours"] = atm_hours
        else:
            item["opening_hours"] = counter_hours
            if atm := atm_hours.as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm

        yield item

    @staticmethod
    def parse_hours(oh: OpeningHours, value: str) -> None:
        # e.g. "平日8:00～21:00<BR>土曜8:00～21:00<BR>日祝8:00～21:00" or "平日9:00～15:00（12/31～1/3は除く）"
        for line in re.split(r"<br\s*/?>", value, flags=re.IGNORECASE):
            line = line.split("（")[0].replace("：", ":")
            if line.startswith("平日"):
                days = DAYS_WEEKDAY
            elif line.startswith("土日"):
                days = ["Sa", "Su"]
            elif line.startswith("土曜"):
                days = ["Sa"]
            elif line.startswith("日"):
                days = ["Su"]
            elif line.startswith("毎日") or line.startswith("全日"):
                days = DAYS
            else:
                continue
            for start_time, end_time in re.findall(r"(\d+:\d+)～(\d+:\d+)", line):
                oh.add_days_range(days, start_time, end_time)
