import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SkylarkJPSpider(Spider):
    name = "skylark_jp"

    start_urls = ["https://store-info.skylark.co.jp/api/point/xn7/"]
    allowed_domains = ["store-info.skylark.co.jp"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            match store["marker"]["ja"]["name"]:
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
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "japanese"
                case "とんから亭":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "tonkatsu"
                case "chawan":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "japanese"
                case "ラ・オハナ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "hawaiian"
                case "魚屋路":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "sushi"
                case "桃菜":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "chinese"
                case "グラッチェガーデンズ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    item["extras"]["brand:en"] = "Grazie Gardens"
                    item.update({"brand_wikidata": "Q120500825"})
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "italian;pizza"
                case "八郎そば":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "soba"
                case "ゆめあん食堂":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "japanese"
                case "三〇三":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "japanese"
                case "グランブッフェ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "buffet"
                case "エクスブルー":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "buffet"
                case "フェスタガーデン":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "buffet"
                case "點心甜心":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "chinese"
                case "包包點心":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "chinese"
                case "ペルティカ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "italian;pasta"
                case "くし葉":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "buffet"
                case "フロプレステージュ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    apply_category(Categories.SHOP_CONFECTIONERY, item)
                case "トマト＆オニオン":
                    item.update({"brand_wikidata": "Q11321395"})
                    apply_category(Categories.RESTAURANT, item)
                case "じゅうじゅうカルビ":
                    item["brand"] = store["marker"]["ja"]["name"]
                    item.update({"brand_wikidata": "Q98798383"})
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "yakiniku"
                case "資さんうどん":
                    item["brand"] = store["marker"]["ja"]["name"]
                    item.update({"brand_wikidata": "Q11634979"})
                    apply_category(Categories.RESTAURANT, item)
                    item["extras"]["cuisine"] = "udon"
                case _:
                    apply_category(Categories.RESTAURANT, item)

            item["branch"] = re.search(r"\S+$", str(store["name"])).group()

            if store["extra_fields"]["全日２４時間フラグ"] == "1":
                item["opening_hours"] = "24/7"

            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, store["extra_fields"]["クレジット（有無）フラグ"] == "1")
            apply_yes_no(Extras.WIFI, item, store["extra_fields"]["ｗｉ－ｆｉ（有無）フラグ"] == "1")
            item["website"] = f"https://store-info.skylark.co.jp/skylark/map/{store['id']}"
            item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
            apply_yes_no("parking", item, store["extra_fields"]["駐車場（有無）フラグ"] == "有")
            item["extras"]["start_date"] = re.search(
                r"\d{4}-\d{2}-\d{2}", str(store["extra_fields"]["オープン日"])
            ).group()
            apply_yes_no("wheelchair", item, store["extra_fields"]["車椅子対応フラグ"] == "1")
            apply_yes_no("reservation", item, store["extra_fields"]["予約フラグ"] == "1")
            if store["extra_fields"]["コンセント席フラグ"] == "1":
                item["extras"]["socket:nema_5_15"] = "yes"
            apply_yes_no("bar", item, store["extra_fields"]["カウンター席フラグ"] == "1")
            apply_yes_no("toilets:wheelchair", item, store["extra_fields"]["多目的トイレフラグ"] == "1")
            apply_yes_no("pets_allowed", item, store["extra_fields"]["ペット同伴可"] == "1")
            if store["extra_fields"]["完全禁煙フラグ"] == "1":
                item["extras"]["smoking"] = "no"
            apply_yes_no("delivery", item, store["extra_fields"]["宅配フラグ"] == "1")
            apply_yes_no("takeaway", item, store["extra_fields"]["持ち帰りフラグ"] == "1")
            apply_yes_no("elevator", item, store["extra_fields"]["エレベーターフラグ"] == "1")
            apply_yes_no("changing_table", item, store["extra_fields"]["おむつ替え台フラグ"] == "1")
            item["name"] = None

            yield item
