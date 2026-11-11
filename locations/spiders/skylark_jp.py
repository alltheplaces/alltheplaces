from typing import Iterable

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class SkylarkJPSpider(GogaStoreLocatorSpider):
    name = "skylark_jp"
    start_urls = ["https://store-info.skylark.co.jp/api/point"]
    geohashes = ["w", "x"]
    geohash_suffix = "/"
    website_formatter = "https://store-info.skylark.co.jp/skylark/map/{}/"

    FLAGS = {
        "クレジット（有無）フラグ": PaymentMethods.CREDIT_CARDS,
        "ｗｉ－ｆｉ（有無）フラグ": Extras.WIFI,
        "駐車場（有無）フラグ": Extras.PARKING,
        "車椅子対応フラグ": Extras.WHEELCHAIR,
        "予約フラグ": Extras.RESERVATION,
        "カウンター席フラグ": Extras.BAR,
        "多目的トイレフラグ": Extras.TOILETS_WHEELCHAIR,
        "ペット同伴可": Extras.PETS_ALLOWED,
        "宅配フラグ": Extras.DELIVERY,
        "持ち帰りフラグ": Extras.TAKEAWAY,
        "エレベーターフラグ": Extras.ELEVATOR,
        "おむつ替え台フラグ": Extras.BABY_CHANGING_TABLE,
    }

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        match source_feature["marker"]["ja"]["name"]:
            case "ガスト":
                item.update({"brand_wikidata": "Q87724117"})
                apply_category(Categories.RESTAURANT, item)
            case "バーミヤン":
                item.update({"brand_wikidata": "Q11328598"})
                apply_category(Categories.RESTAURANT, item)
            case "しゃぶ葉":
                item.update({"brand_wikidata": "Q67710247"})
                apply_category(Categories.RESTAURANT, item)
            case "夢庵":
                item.update({"brand_wikidata": "Q11253593"})
                apply_category(Categories.RESTAURANT, item)
            case "ジョナサン":
                item.update({"brand_wikidata": "Q11310628"})
                apply_category(Categories.RESTAURANT, item)
            case "ステーキガスト":
                item.update({"brand_wikidata": "Q92599119"})
                apply_category(Categories.RESTAURANT, item)
            case "むさしの森珈琲":
                item.update({"brand_wikidata": "Q116758676"})
                apply_category(Categories.CAFE, item)
            case "から好し（単独店）":
                item.update({"brand_wikidata": "Q115008407"})
                apply_category(Categories.RESTAURANT, item)
            case "藍屋":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "japanese"
            case "とんから亭":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "tonkatsu"
            case "chawan":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "japanese"
            case "ラ・オハナ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "hawaiian"
            case "魚屋路":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "sushi"
            case "桃菜":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "chinese"
            case "グラッチェガーデンズ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                item["extras"]["brand:en"] = "Grazie Gardens"
                item.update({"brand_wikidata": "Q120500825"})
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "italian;pizza"
            case "八郎そば":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "soba"
            case "ゆめあん食堂":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "japanese"
            case "三〇三":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "japanese"
            case "グランブッフェ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "buffet"
            case "エクスブルー":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "buffet"
            case "フェスタガーデン":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "buffet"
            case "點心甜心":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "chinese"
            case "包包點心":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "chinese"
            case "ペルティカ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "italian;pasta"
            case "くし葉":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "buffet"
            case "フロプレステージュ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                apply_category(Categories.SHOP_CONFECTIONERY, item)
            case "トマト＆オニオン":
                item.update({"brand_wikidata": "Q11321395"})
                apply_category(Categories.RESTAURANT, item)
            case "じゅうじゅうカルビ":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                item.update({"brand_wikidata": "Q98798383"})
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "yakiniku"
            case "資さんうどん":
                item["brand"] = source_feature["marker"]["ja"]["name"]
                item.update({"brand_wikidata": "Q11634979"})
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "udon"
            case _:
                apply_category(Categories.RESTAURANT, item)

        item["branch"] = item.pop("name").split()[-1]
        item["extras"]["start_date"] = source_feature["オープン日"][:10]

        item["opening_hours"] = OpeningHours()
        if source_feature["全日２４時間フラグ"] == "1":
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        else:
            for days, key in [(DAYS_WEEKDAY, "平日"), (["Sa"], "土曜日"), (["Su"], "日曜・祝日")]:
                item["opening_hours"].add_days_range(days, *source_feature[key].split("～"))

        for key, attribute in self.FLAGS.items():
            apply_yes_no(attribute, item, source_feature[key] == "1")
        if source_feature["コンセント席フラグ"] == "1":
            item["extras"]["socket:nema_1_15"] = "yes"
        if source_feature["完全禁煙フラグ"] == "1":
            item["extras"]["smoking"] = "no"

        yield item
