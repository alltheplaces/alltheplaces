import re
import unicodedata
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider

TIME_RANGE = r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})"


class PalclosetSpider(GogaStoreLocatorSpider):
    name = "palcloset"
    skip_auto_cc_domain = True
    start_urls = ["https://palcloset.storelocator.jp/api/point"]
    geohashes = ["w", "x", "z"]
    geohash_suffix = "/"

    # Labels in front of a time range; public holidays (祝) are not kept.
    DAY_LABELS = {
        "平日": DAYS_WEEKDAY,
        "月-金": DAYS_WEEKDAY,
        "平日・土": DAYS[:6],
        "月-土": DAYS[:6],
        "土日祝": DAYS_WEEKEND,
        "土日祝日": DAYS_WEEKEND,
        "土日/祝": DAYS_WEEKEND,
        "日": ["Su"],
        "日祝": ["Su"],
        "日・祝": ["Su"],
        "日・祝日": ["Su"],
        "日-祝": ["Su"],
    }
    NOTICE = "※臨時休業及び営業時間を変更している場合がございます。詳しくは各館HP、店舗へご確認くださいませ。"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        match source_feature["代表ブランド名"]:
            case "3COINS":
                item["brand_wikidata"] = "Q60997353"
                apply_category(Categories.SHOP_VARIETY_STORE, item)
            case _:
                item["brand"] = source_feature["代表ブランド名"]
                apply_category(Categories.SHOP_CLOTHES, item)

        item["website"] = (
            f"https://www.palcloset.jp/addons/pal/shoplist/detail/?brandshop_no={source_feature['key']}&b={source_feature['代表ブランドコード']}"
        )
        item["postcode"] = source_feature["郵便番号"]
        if item["phone"] == "-":
            item["phone"] = None
        item["extras"]["addr:province"] = item.pop("state")
        item["branch"] = item.pop("name")

        # Almost every shop has irregular closing days (不定休); fixed closing days are not handled.
        if source_feature["定休日"] in ("不定休", "年中無休", ""):
            item["opening_hours"] = self.parse_opening_hours(source_feature["営業時間"])

        yield item

    def parse_opening_hours(self, value: str) -> OpeningHours | None:
        text = unicodedata.normalize("NFKC", value).replace(self.NOTICE, "")
        text = re.sub(r"[~〜‐ー]", "-", re.sub(r"[\s【】※、]", "", text))
        text = re.sub(r"(?<=\D):", "", text)
        if not re.fullmatch(rf"(?:\D*?{TIME_RANGE})+", text):
            return None

        # A leading range without a label covers every day; labelled ranges after it override some days.
        hours = {}
        for index, (label, start, end) in enumerate(re.findall(rf"(\D*?){TIME_RANGE}", text)):
            if index == 0 and label == "":
                days = DAYS
            elif label in self.DAY_LABELS:
                days = self.DAY_LABELS[label]
            else:
                return None
            hours.update({day: (start, end) for day in days})

        oh = OpeningHours()
        for day, (start, end) in hours.items():
            oh.add_range(day, start, end)
        return oh
