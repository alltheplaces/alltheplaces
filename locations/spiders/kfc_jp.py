import re
from typing import Iterable

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider

HOURS_REGEX = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")


class KfcJPSpider(GogaStoreLocatorSpider):
    name = "kfc_jp"
    item_attributes = {"brand_wikidata": "Q524757"}
    start_urls = ["https://search.kfc.co.jp/api/points"]
    geohashes = ["x", "w", "z"]
    website_formatter = "https://search.kfc.co.jp/points/{}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["postcode"] = source_feature["郵便番号"]
        item["city"] = source_feature["市区町村"]
        oh = OpeningHours()
        for days, key in ((DAYS_WEEKDAY, "平日営業時間"), (DAYS_WEEKEND, "土日祝営業時間")):
            if match := HOURS_REGEX.match(source_feature.get(key) or ""):
                oh.add_days_range(days, *match.groups())
        if oh.day_hours:
            item["opening_hours"] = oh
        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.DRIVE_THROUGH, item, source_feature.get("ドライブスルー"), False)
        apply_yes_no(Extras.DELIVERY, item, source_feature.get("お届けケンタッキー") == "1", False)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, source_feature.get("クレジットカード"), False)
        apply_yes_no(PaymentMethods.PAYPAY, item, source_feature.get("QRコード決済"), False)
        yield item
