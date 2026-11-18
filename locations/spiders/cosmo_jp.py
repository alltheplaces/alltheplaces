import re
import unicodedata
from typing import Iterable

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class CosmoJPSpider(GogaStoreLocatorSpider):
    name = "cosmo_jp"

    start_urls = ["https://map.cosmo-energy.co.jp/api/points"]
    item_attributes = {
        "brand_wikidata": "Q2498318",
    }

    FLAGS = {
        "フル": "full_service",
        "セルフ": "self_service",
        "車検": Extras.VEHICLE_INSPECTION_SERVICES,
        "洗車": Extras.CAR_WASH,
        "EV急速充電器": Fuel.ELECTRIC,
        "セブン-イレブン複合店": "sells:food",
        "Id": PaymentMethods.ID,
        "WAON": PaymentMethods.WAON,
        "PayPay": PaymentMethods.PAYPAY,
        "QUICPay": PaymentMethods.QUICPAY,
        "d払い": PaymentMethods.D_BARAI,
        "楽天ペイ": PaymentMethods.RAKUTEN_PAY,
    }
    HOURS_FIELDS = {
        "営業時間(平日)": DAYS_WEEKDAY,
        "営業時間(土曜日)": ["Sa"],
        "営業時間(日曜日)": ["Su"],
    }
    TIME_RANGE = re.compile(r"^(\d{1,2}:\d{2})\s*[~〜-]\s*翌?(\d{1,2}:\d{2})$")

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = "コスモ"
        item["branch"] = source_feature["name"].removesuffix("ＳＳ")
        item["extras"]["branch:ja-Hira"] = source_feature.get("店名カナ")
        item["website"] = source_feature.get("確認用URL")

        for key, attribute in self.FLAGS.items():
            apply_yes_no(attribute, item, source_feature.get(key) == "1")

        if source_feature.get("24時間営業") == "1":
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = self.parse_opening_hours(source_feature)

        apply_category(Categories.FUEL_STATION, item)

        yield item

    def parse_opening_hours(self, source_feature: dict) -> OpeningHours | None:
        oh = OpeningHours()
        days_with_hours = set()
        for field, days in self.HOURS_FIELDS.items():
            value = unicodedata.normalize("NFKC", source_feature.get(field) or "").strip()
            if match := self.TIME_RANGE.match(value):
                oh.add_days_range(days, match.group(1), match.group(2))
                days_with_hours.update(days)

        # Only trust the result when the weekday hours could be read.
        if not days_with_hours.issuperset(DAYS_WEEKDAY):
            return None

        for day in self.parse_closed_days(source_feature.get("定休日")):
            if day not in days_with_hours:
                oh.set_closed(day)

        return oh

    @staticmethod
    def parse_closed_days(value: str | None) -> list[str]:
        """Read simple values such as "日曜", "毎週日曜日" or "土曜、日曜、祝日".

        Anything else (nth Sundays, New Year, notes) returns no days.
        """
        closed = []
        for token in re.split(r"[、・]", unicodedata.normalize("NFKC", value or "").strip()):
            token = token.removeprefix("毎週").removeprefix("毎")
            if token in ("祝日", "祝"):
                continue
            if token.endswith("曜"):
                token += "日"
            if token.endswith("曜日") and (day := DAYS_JP.get(token)):
                closed.append(day)
            else:
                return []
        return closed
