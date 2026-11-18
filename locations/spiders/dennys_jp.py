from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class DennysJPSpider(GogaStoreLocatorSpider):
    name = "dennys_jp"
    item_attributes = {"brand": "デニーズ", "brand_wikidata": "Q11320661"}
    start_urls = ["https://shop.dennys.co.jp/api/point"]
    geohashes = ["w", "x", "z"]
    geohash_suffix = "/"
    website_formatter = "https://shop.dennys.co.jp/map/{}/"

    FLAGS = {
        "駐車場あり": Extras.PARKING,
        "だれでもトイレ": Extras.TOILETS_WHEELCHAIR,
        "ベビーシート": Extras.BABY_CHANGING_TABLE,
        "出前サービス": Extras.DELIVERY,
        "エレベーター": Extras.ELEVATOR,
        "車椅子対応の入り口": Extras.WHEELCHAIR,
    }

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("デニーズ", "").split()[0]
        item["phone"] = f"+81 {source_feature['電話番号']}"
        apply_category(Categories.RESTAURANT, item)

        item["opening_hours"] = OpeningHours()
        for day_name, day in DAYS_JP.items():
            if not day_name.endswith("曜日"):
                continue
            ranges = [hours.strip().split("-") for hours in source_feature[f"{day_name}の営業時間"].split(",")]
            for open_time, close_time in ranges:
                # After-midnight hours are listed on the day the night started, so move them to the next day
                overflow = len(ranges) > 1 and open_time in ("0:00", "00:00")
                item["opening_hours"].add_range(DAYS[(DAYS.index(day) + overflow) % 7], open_time, close_time)

        for key, attribute in self.FLAGS.items():
            apply_yes_no(attribute, item, source_feature[key] == "1")
        if source_feature["コンセント"] == "1":
            item["extras"]["socket:nema_1_15"] = "yes"
        if source_feature["全席禁煙"] == "1":
            item["extras"]["smoking"] = "no"

        yield item
