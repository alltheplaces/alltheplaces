import re
from typing import Iterable

from locations.categories import Categories, Drink, Extras, PaymentMethods, Sells, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider, parse_opening_hours


class NewdaysJPSpider(LocationCloudSpider):
    name = "newdays_jp"
    item_attributes = {"brand": "NewDays", "brand_wikidata": "Q11234763"}
    api_endpoint = "https://shop.jr-cross.co.jp/eki/api/proxy2/shop/list"
    additional_args = "&c_d137=1&add=detail&device=pc&sort=yomi&ex-code=only.prior"
    website_formatter = "https://shop.jr-cross.co.jp/eki/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = _strip_brand(source_feature["name"])
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = re.sub(r"^[0-9]+", "", ruby).removeprefix("ニューデイズ")
        if phone := source_feature.get("phone"):
            item["phone"] = f"+81 {phone}"

        texts = {t["label"]: t["value"] for t in source_feature.get("details", [{}])[0].get("texts", [])}
        flags = {f["label"]: f["value"] for f in source_feature.get("details", [{}])[0].get("flags", [])}

        if flags.get("閉店"):
            return  # permanently closed store: do not write to OSM

        if opening_hours := parse_opening_hours(texts):
            item["opening_hours"] = opening_hours

        apply_yes_no(PaymentMethods.SUICA, item, flags.get("Suica決済"))
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, flags.get("クレジット決済"))
        apply_yes_no(Sells.ALCOHOL, item, flags.get("お酒"))
        apply_yes_no(Sells.TOBACCO, item, flags.get("たばこ"))
        apply_yes_no(Drink.COFFEE, item, flags.get("カウンターコーヒー"))
        apply_yes_no(Drink.BEER, item, flags.get("生ビール"))
        apply_yes_no(Extras.ATM, item, flags.get("ATM"))
        apply_yes_no(Extras.WIFI, item, flags.get("WiFi"))
        apply_yes_no(Extras.SELF_CHECKOUT, item, flags.get("セルフレジ設置店舗"))
        apply_yes_no(Extras.INDOOR_SEATING, item, flags.get("イートイン"))
        apply_yes_no(Extras.DUTY_FREE, item, flags.get("免税対応／Tax Free"))

        # Detail flags deliberately not mapped to OSM tags:
        #   00001 東京                        (regional division)
        #   00002 新宿                        (regional division)
        #   00004 横浜                        (regional division)
        #   00005 八王子                      (regional division)
        #   00006 大宮                        (regional division)
        #   00007 千葉                        (regional division)
        #   00008 高崎                        (regional division)
        #   00009 水戸                        (regional division)
        #   00010 仙台                        (regional division)
        #   00011 盛岡                        (regional division)
        #   00012 新潟                        (regional division)
        #   00013 長野                        (regional division)
        #   00071 JRE POINT Suica加盟店       (programme membership)
        #   00072 JRE POINT 加盟店            (programme membership)
        #   00076 ホットスナック              (product)
        #   00078 中華まん                    (product)
        #   00100 他社Suica端末(社内)         (payment terminal)
        #   00101 オールセルフレジ店舗        (facility)
        #   00112 休業                        (temporarily closed)
        #   00129 禁煙                        (facility)
        #   00130 専用室                      (smoking room)
        #   00131 可能室                      (smoking room)
        #   00132 加熱式可                    (smoking)
        #   00134 電源                        (facility)
        #   00137 ND・NDK                     (operational division)
        #   00138 専門店直営                  (operational division)
        #   00139 専門店委託                  (operational division)
        #   00140 foods外食                  (operational division)
        #   00141 foods弁当                  (operational division)
        #   00142 プロジェクト                (operational division)
        #   00143 商業施設・フードコート      (operational division)
        #   00146 ベビーチェア                (facility)
        #   00147 ベビーカー入店可            (facility)
        #   00148 車いす入店可                (facility)
        #   00153 専門店東エリア              (regional division)
        #   00154 専門店西エリア              (regional division)
        #   00155 営業部                      (operational division)
        #   00156 専門店南エリア              (regional division)
        #   00158 【管理】リテールCP_R-ND     (management)
        #   00159 【管理】フーズCP            (management)
        #   00163 【管理】リテールCP_R-専門店 (management)
        #   00165 収納代行                    (facility)
        #   00002 新宿                        (regional division)
        #   00004 横浜                        (regional division)
        #   00005 八王子                      (regional division)
        #   00006 大宮                        (regional division)
        #   00007 千葉                        (regional division)
        #   00008 高崎                        (regional division)
        #   00009 水戸                        (regional division)
        #   00010 仙台                        (regional division)
        #   00011 盛岡                        (regional division)
        #   00012 新潟                        (regional division)
        #   00013 長野                        (regional division)
        #   00071 JRE POINT Suica加盟店       (programme membership)
        #   00072 JRE POINT 加盟店            (programme membership)
        #   00076 ホットスナック              (product)
        #   00078 中華まん                    (product)
        #   00100 他社Suica端末(社内)         (payment terminal)
        #   00101 オールセルフレジ店舗        (facility)
        #   00112 休業                        (temporarily closed)
        #   00129 禁煙                        (facility)
        #   00130 専用室                      (smoking room)
        #   00131 可能室                      (smoking room)
        #   00132 加熱式可                    (smoking)
        #   00134 電源                        (facility)
        #   00137 ND・NDK                     (operational division)
        #   00138 専門店直営                  (operational division)
        #   00139 専門店委託                  (operational division)
        #   00140 foods外食                  (operational division)
        #   00141 foods弁当                  (operational division)
        #   00142 プロジェクト                (operational division)
        #   00143 商業施設・フードコート      (operational division)
        #   00146 ベビーチェア                (facility)
        #   00147 ベビーカー入店可            (facility)
        #   00148 車いす入店可                (facility)
        #   00153 専門店東エリア              (regional division)
        #   00154 専門店西エリア              (regional division)
        #   00155 営業部                      (operational division)
        #   00156 専門店南エリア              (regional division)
        #   00158 【管理】リテールCP_R-ND     (management)
        #   00159 【管理】フーズCP            (management)
        #   00163 【管理】リテールCP_R-専門店 (management)
        #   00165 収納代行                    (facility)

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item


def _strip_brand(name: str) -> str:
    brand_prefixes = (
        "NewDays KIOSK ",
        "NewDays ",
        "NewDaysミニ ",
        "NewDaysミニ",
        "KIOSK ",
        "NewDays＋HANAGATAYA ",
    )
    for prefix in brand_prefixes:
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name
