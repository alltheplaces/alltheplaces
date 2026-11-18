import re
import unicodedata
from typing import Iterable

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class SeimsJPSpider(GogaStoreLocatorSpider):
    name = "seims_jp"

    start_urls = ["https://store.seims.co.jp/api/point"]
    geohashes = ["w", "x", "z"]
    geohash_suffix = "/"
    website_formatter = "https://store.seims.co.jp/map/{}/"

    TIME_RANGE = re.compile(r"^(\d{1,2}:\d{2})~(\d{1,2}:\d{2})$")
    # The 24 hour stores add a note about the hour they close, which the ranges already show.
    CLOSED_HOUR_NOTE = re.compile(r"※\d{1,2}:\d{2}~\d{1,2}:\d{2}は休業$")

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        match source_feature["marker"]["ja"]["name"]:
            case "ドラッグセイムス":
                item["brand_wikidata"] = "Q11456137"
            case "ドラッグユタカ":
                item["brand"] = "ドラッグユタカ"  # complicated NSI
                item["brand_wikidata"] = "Q11345601"
            case "アメリカンドラッグ":
                item["brand"] = "アメリカンドラッグ"
                item["brand_wikidata"] = "Q11285057"  # no NSI
            case _:
                item["brand"] = source_feature["marker"]["ja"]["name"]  # the others have no Wikidata

        if match := re.search(r"(?:\s)\b\S+$", str(source_feature["name"])):
            item["branch"] = match.group()
            del item["name"]

        item["extras"]["addr:province"] = item.pop("state")
        item["extras"]["branch:ja-Hira"] = source_feature["店名かな"]

        if source_feature["電話番号"] is not None:
            item["phone"] = f"+81 {source_feature['電話番号']}"
            if source_feature["調剤電話番号"] is not None:
                item["extras"]["phone:pharmacy"] = f"+81 {source_feature['調剤電話番号']}"
        else:
            item["phone"] = f"+81 {source_feature['調剤電話番号']}"

        apply_yes_no("drinking_water:refill", item, source_feature["給水器"] == "1")
        apply_yes_no("drive_through", item, source_feature["【調剤】調剤ドライブスルー"] == "1")

        apply_yes_no("sells:rice", item, source_feature["【取扱】米"] == "1")
        apply_yes_no("sells:meat", item, source_feature["【取扱】精肉"] == "1")
        apply_yes_no("sells:pet_supplies", item, source_feature["【取扱】ペット用品"] == "1")
        apply_yes_no("sells:dairy", item, source_feature["【取扱】乳製品"] == "1")
        apply_yes_no("sells:frozen_food", item, source_feature["【取扱】冷凍食品"] == "1")
        apply_yes_no("sells:produce", item, source_feature["【取扱】青果"] == "1")
        apply_yes_no("sells:alcohol", item, source_feature["【取扱】酒類"] == "1")
        apply_yes_no("sells:contact_lenses", item, source_feature["【取扱】コンタクトレンズ"] == "1")
        apply_yes_no("sells:baby_goods", item, source_feature["【取扱】ベビー用品"] == "1")

        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, source_feature["【支払】ｸﾚｼﾞｯﾄ"] == "1")
        apply_yes_no(PaymentMethods.CONTACTLESS, item, source_feature["【支払】ｸﾚｼﾞｯﾄ(タッチ決済)"] == "1")

        if parking := "".join(filter(str.isdigit, str(source_feature["駐車場台数"]))).lstrip("0"):
            item["extras"]["parking:capacity:standard"] = parking

        item["extras"]["website:booking"] = source_feature["【調剤】処方せんネット受付URL"]

        drugstore_hours = self.parse_opening_hours(source_feature["営業時間（ドラッグストア）"])
        pharmacy_hours = self.parse_opening_hours(source_feature["営業時間（調剤）"])
        if source_feature["ドラッグストア"] == "1":
            apply_category(Categories.SHOP_CHEMIST, item)
            item["opening_hours"] = drugstore_hours
        if source_feature["処方せん受付店舗"] == "1":
            apply_category(Categories.PHARMACY, item)
            item["extras"]["dispensing"] = "yes"
            if source_feature["ドラッグストア"] == "1":
                if pharmacy_hours:
                    item["extras"]["opening_hours:pharmacy"] = pharmacy_hours.as_opening_hours()
            else:
                item["opening_hours"] = pharmacy_hours

        yield item

    def parse_opening_hours(self, value: str | None) -> OpeningHours | None:
        text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).lstrip("'").replace("〜", "~")
        text = self.CLOSED_HOUR_NOTE.sub("", text)
        if not text:
            return None
        oh = OpeningHours()
        for part in text.split("/"):
            days = DAYS
            if "曜" in part:
                day_text, part = part.split(":", 1)
                days = []
                for token in day_text.split("・"):
                    if token == "祝日":
                        continue
                    start, _, end = token.partition("~")
                    if not (start_day := DAYS_JP.get(start)) or (end and not (end_day := DAYS_JP.get(end))):
                        return None
                    days += day_range(start_day, end_day) if end else [start_day]
            for time_range in part.split("、"):
                if not (match := self.TIME_RANGE.match(time_range)):
                    return None
                oh.add_days_range(days, match.group(1), match.group(2))
        return oh
