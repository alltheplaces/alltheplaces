from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_JP, OpeningHours
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class OgakiKyoritsuBankJPSpider(GogaStoreLocatorSpider):
    name = "ogaki_kyoritsu_bank_jp"

    start_urls = ["https://store.okb.co.jp/api/points"]
    item_attributes = {
        "brand": "大垣共立銀行",
        "brand_wikidata": "Q11433765",
        "name": "大垣共立銀行",
        "extras": {"brand:en": "Ogaki Kyoritsu Bank", "brand:ja": "大垣共立銀行"},
    }
    website_formatter = "https://store.okb.co.jp/points/{}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        match source_feature["markers"]["ja"]:
            case "3":
                apply_category(Categories.BANK, item)
                item["opening_hours"] = self.parse_opening_hours(source_feature, "店舗営業時間")
                if atm_hours := self.parse_opening_hours(source_feature, "ATM営業時間"):
                    apply_yes_no(Extras.ATM, item, True)
                    item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()
            case "8":
                apply_category(Categories.OFFICE_FINANCIAL, item)
                item["opening_hours"] = self.parse_opening_hours(source_feature, "店舗営業時間")
            case "9":
                apply_category(Categories.ATM, item)
                item["opening_hours"] = self.parse_opening_hours(source_feature, "ATM営業時間")
            case _:
                # Marker 11 mixes overseas representative offices with domestic consultation desks.
                return

        item["branch"] = source_feature["name"]
        del item["name"]
        item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(source_feature["店舗名(よみ)"])
        if postcode := source_feature.get("郵便番号"):
            item["postcode"] = postcode

        yield item

    def parse_opening_hours(self, source_feature: dict, prefix: str) -> OpeningHours | None:
        oh = OpeningHours()
        has_hours = False
        for day_name, day in DAYS_JP.items():
            if not day_name.endswith("曜日"):
                continue
            if value := source_feature.get(f"{prefix}{day_name}"):
                has_hours = True
                for time_range in value.split(","):
                    open_time, close_time = time_range.split("-")
                    oh.add_range(day, open_time, close_time)
            else:
                oh.set_closed(day)
        return oh if has_hours else None
