import json
from collections.abc import Iterable

from chompjs import parse_js_object

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.geo import postal_regions
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

BRANDS = {
    "01": {
        "brand": "welcia",
        "brand_wikidata": "Q11288687",
        "name": "ウエルシア薬局",
        "branch_prefixes": ["ウエルシア", "薬局"],
        "ruby_prefixes": ["ウエルシア", "薬局"],
    },
    "02": {
        "brand": "ハックドラッグ",
        "brand_wikidata": "",
        "branch_prefixes": ["ハックドラッグ"],
        "ruby_prefixes": ["ハックドラッグ"],
    },
    "03": {
        "brand": "ダックス",
        "brand_wikidata": "",
        "branch_prefixes": ["薬局ダックス", "ダックス"],
        "ruby_prefixes": ["ダックス"],
    },
    "04": {
        "brand": "ハッピードラッグ",
        "brand_wikidata": "Q11368084",
        "branch_prefixes": ["ハッピー・ドラッグ", "ハッピー調剤薬局", "ハッピードラッグ"],
        "ruby_prefixes": ["ハッピードラッグ"],
    },
    "05": {
        "brand": "カラースタジオ",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["カラースタジオ"],
        "ruby_prefixes": ["カラースタジオ"],
    },
    "06": {
        "brand": "金光薬品",
        "brand_wikidata": "Q11646466",
        "branch_prefixes": ["金光薬品", "金光薬局"],
        "ruby_prefixes": ["カネミツヤッキョク"],
    },
    "07": {
        "brand": "マサヤ",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["マサヤ "],
    },
    "08": {
        "brand": "よどやドラッグ",
        "brand_wikidata": "Q11281187",
        "branch_prefixes": ["よどやドラッグ"],
    },
    "09": {
        "brand": "マルエドラッグ",
        "brand_wikidata": "Q11298666",
        "branch_prefixes": ["マルエドラッグ", "マルエ薬局"],
    },
    "10": {
        "brand": "アリエールLAUNDRY PRO",
        "brand_wikidata": "",
        "category": Categories.SHOP_COUNTRY_STORE,
        "branch_prefixes": ["アリエールLAUNDRY PRO "],
        "ruby_prefixes": ["アリエールランドリープロ"],
    },
    "11": {
        "brand": "ププレひまわり",
        "brand_wikidata": "Q119871972",
        "branch_prefixes": [
            "スーパードラッグひまわり",
            "フード＆ドラッグひまわり",
            "ププレひまわり薬局",
            "ププレひまわり",
        ],
    },
    "12": {
        "brand": "NARCIS",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["NARCIS"],
        "ruby_prefixes": ["ナルシス"],
    },
    "13": {
        "brand": "コクミン",
        "brand_wikidata": "Q11301923",
        "branch_prefixes": [
            "KoKuMiN",
            "コクミンドラッグ",
            "コクミン薬局",
            "コクミン",
            "FamilyMart+コクミンドラッグ",
            "AIRPORT＋DRUG",
            "AIRPORT+DRUG ",
            "CityDrug ",
            "KeiyoDrug ",
        ],
    },
    "14": {
        "brand": "アルビオンドレッサー",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["アルビオンドレッサー"],
    },
    "15": {
        "brand": "アトリエアルビオン",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["アトリエアルビオン"],
    },
    "16": {
        "brand": "ふく薬品",
        "brand_wikidata": "Q119380891",
        "branch_prefixes": ["ふく薬品", "ふく薬局"],
        "strip": True,
    },
    "18": {
        "brand": "Zoomore",
        "brand_wikidata": "",
        "category": Categories.SHOP_PET,
        "branch_prefixes": ["Zoomore"],
        "ruby_prefixes": ["ズーモア"],
    },
    "19": {
        "brand": "コスメテリア",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["コスメテリア"],
    },
    "20": {
        "brand": "とをしや薬局",
        "brand_wikidata": "Q11273556",
        "branch_prefixes": ["とをしや"],
        "removesuffix": "とをしや薬局",
    },
    "21": {
        "brand": "ウェルパーク",
        "brand_wikidata": "Q11288610",
        "branch_prefixes": ["ウェルパーク", "薬局"],
        "ruby_prefixes": ["ウェルパーク", "薬局"],
    },
}

# flag code -> OSM payment tag
PAYMENT_METHODS = {
    "00010": PaymentMethods.ALIPAY,
    "00011": PaymentMethods.AMERICAN_EXPRESS,
    "00012": "payment:bank_pay",
    "00013": PaymentMethods.DINERS_CLUB,
    "00014": PaymentMethods.DISCOVER_CARD,
    "00016": "payment:icoca",
    "00017": PaymentMethods.JCB,
    "00018": "payment:j_coin_pay",
    "00019": "payment:kitaca",
    "00021": "payment:manaca",
    "00022": PaymentMethods.MASTER_CARD,
    "00023": PaymentMethods.MERPAY,
    "00024": "payment:pasmo",
    "00025": PaymentMethods.PAYPAY,
    "00026": PaymentMethods.QUICPAY,
    "00027": PaymentMethods.EDY,
    "00028": PaymentMethods.RAKUTEN_PAY,
    "00029": "payment:sugoca",
    "00030": "payment:suica",
    "00031": "payment:toica",
    "00032": PaymentMethods.UNIONPAY,
    "00033": PaymentMethods.VISA,
    "00034": PaymentMethods.WAON,
    "00035": PaymentMethods.WECHAT,
    "00036": PaymentMethods.D_BARAI,
    "00078": PaymentMethods.CREDIT_CARDS,
    "00079": PaymentMethods.WAON,
    "00080": PaymentMethods.EDY,
    "00081": PaymentMethods.UNIONPAY,
    "00082": "payment:icsf",
    "00083": PaymentMethods.QUICPAY,
    "00085": PaymentMethods.ALIPAY,
    "00086": PaymentMethods.D_BARAI,
    "00087": PaymentMethods.WECHAT,
    "00088": PaymentMethods.PAYPAY,
    "00089": "payment:au_pay",
    "00090": PaymentMethods.RAKUTEN_PAY,
    "00091": "payment:resona_wallet",
    "00092": "payment:yucho_pay",
    "00093": PaymentMethods.MERPAY,
    "00094": "payment:j_coin_pay",
    "00095": "payment:fami_pay",
    "00096": "payment:bank_pay",
    "00097": "payment:smart_code",
    "00230": "payment:quo_pay",
    "00231": "payment:aeon_pay",
    "00255": "payment:pitapa",
}

# service-flag / detail-field code -> meaning (ref. welcia_detail_page.md)
FLAG_CLOSED = "00147"  # 閉店 -> remove from dataset when true
FLAG_FAX = "00040"  # Fax番号
FLAG_TOILETS_OSTOMY = "00056"  # オストメイトトイレ
FLAG_ALCOHOL = "00057"  # お酒
FLAG_DUTY_FREE = "00062"  # 免税
FLAG_PARKING = "00065"  # 駐車場
FLAG_DISPENSING = "00076"  # 調剤受付
FLAG_DEDICATED_PHARMACY = "00077"  # 調剤専門店
FLAG_PHARMACY_PHONE = "00114"  # 調剤薬局電話番号
FLAG_PHARMACY_FAX = "00110"  # 調剤薬局Fax番号
FLAG_UBER_EATS = "00228"  # Uber Eats デリバリー
FLAG_STORE_HOURS = "00007"  # 営業時間
FLAG_PHARMACY_HOURS = "00112"  # 調剤薬局営業時間


class WelciaJPSpider(LocationCloudSpider):
    name = "welcia_jp"
    api_endpoint = "https://store.welcia.co.jp/welcia/api/proxy2/shop/list"
    website_formatter = "https://store.welcia.co.jp/welcia/spot/detail?code={}"

    """
    example:
    {
        "code": "1001D",
        "name": "ウエルシア春日部一ノ割店",
        "ruby": "ウエルシアカスカベイチノワリテン", // 822 stores have non-empty ruby / 2144 has no 'ruby' key
        "phone": "048-735-4739",
        "address_name": "埼玉県春日部市一ノ割1-11-20",
        "address_code": "11214", // municipality code / 11214 === 埼玉県春日部市
                                 // ref. 市区町村コードから探す(市区町村) | 政府統計の総合窓口 - https://www.e-stat.go.jp/municipalities/cities/areacodesearch?date_year=2026&date_month=8&date_day=29&ht=11214&op=search&keyword_kd=code&item%5B%5D=htCode&item%5B%5D=todoNm&item%5B%5D=parentCityNm&item%5B%5D=parentCityKana&item%5B%5D=selfCityNm&item%5B%5D=selfCityKana&item%5B%5D=htCodeSDate&item%5B%5D=jiyuId&sort%5B%5D=htCode-asc&choices_to_show%5B%5D=cityType&choices_to_show%5B%5D=kasoFlg&choices_to_show%5B%5D=htCodeKokujiDate&choices_to_show%5B%5D=htCodeKokujiNo&choices_to_show%5B%5D=htCodeEDate&choices_to_sort%5B%5D=kasoFlg&choices_to_sort%5B%5D=htCodeSDate&choices_to_sort%5B%5D=htCodeEDate&choices_to_sort%5B%5D=htCodeKokujiDate&choices_to_sort%5B%5D=htCodeKokujiNo&choices_to_sort_value%5B%5D=htCode-desc&choices_to_sort_value%5B%5D=kasoFlg-asc&choices_to_sort_value%5B%5D=kasoFlg-desc&choices_to_sort_value%5B%5D=htCodeSDate-asc&choices_to_sort_value%5B%5D=htCodeSDate-desc&choices_to_sort_value%5B%5D=htCodeEDate-asc&choices_to_sort_value%5B%5D=htCodeEDate-desc&choices_to_sort_value%5B%5D=htCodeKokujiDate-asc&choices_to_sort_value%5B%5D=htCodeKokujiDate-desc&choices_to_sort_value%5B%5D=htCodeKokujiNo-asc&choices_to_sort_value%5B%5D=htCodeKokujiNo-desc&form_id=city_areacode_search_form&source=setup&page=
        "postal_code": "3440031",
        "coord": {
            "lon": 139.768752,
            "lat": 35.960414
        },
        "status": "normal", // always "normal". purpose is unknown
        "list_no": 0, // always 0. purpose is unknown
        "external_code": "1001D", // external_code === code for all first 500 shops
        "categories": [ // always array.length === 1
            {
                "code": "01", // STRING! 21 brand codes, corresponding to next 'name'
                "name": "ウエルシア", // alias for code
                "level": "large", // always 'large'
                "last_update": "2023-10-12T20:22:57+09:00"
            }
        ],
        "last_update": "2026-08-21T16:34:05+09:00"
    }
    """

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        """
        NARCIS = 9 stores, luxury  cosmetic business, transferred to MASAYA.
        ref. NARCIS事業承継完了およびウェブサイト統合に関するお知らせ | COLOR STUDIO・MASAYA | カラースタジオ・マサヤ - https://colorstudio.co.jp/news/
        Zoomore is a pet shop business brand by Welcia.
        ハックドラッグ (HAC drug) was a brand by CFS corporation, which was merged by Welcia, but those 12 store keep the old brand name.
        ref. ウエルシア薬局 - Wikipedia - https://ja.wikipedia.org/wiki/%E3%82%A6%E3%82%A8%E3%83%AB%E3%82%B7%E3%82%A2%E8%96%AC%E5%B1%80#%E6%8C%81%E6%A0%AA%E4%BC%9A%E7%A4%BE%E3%81%AE%E8%A8%AD%E7%AB%8B%E5%BE%8C
        """
        if phone := source_feature.get("phone"):
            item["phone"] = f"+81 {phone}"

        if postal_code := source_feature.get("postal_code"):
            self._apply_postal_address(item, postal_code)

        brand = BRANDS.get(source_feature["categories"][0]["code"])
        if brand is None:
            return

        if brand_name := brand.get("brand"):
            item["brand"] = brand_name
            if brand.get("name"):
                item["name"] = brand["name"]
            else:
                item["name"] = brand_name
        if "brand_wikidata" in brand:
            item["brand_wikidata"] = brand["brand_wikidata"]
        if category := brand.get("category"):
            apply_category(category, item)
        else:
            apply_category(Categories.SHOP_CHEMIST, item)

        self._apply_branch_and_ruby(item, source_feature, brand)

        if branch := item.get("branch"):
            item["branch"] = branch.removesuffix(" (調剤薬局)").removesuffix("(調剤薬局)").strip()

        yield item

    def _apply_postal_address(self, item: Feature, postal_code: str) -> None:
        if region := POSTAL_LOOKUP.get(postal_code):
            item["extras"]["addr:province"] = region["province:ja"]
            item["city"] = region["city:ja"]
            if quarter := region.get("quarter:ja"):
                item["extras"]["addr:quarter"] = quarter
            elif neighbourhood := region.get("neighbourhood:ja"):
                item["extras"]["addr:neighbourhood"] = neighbourhood

    def _apply_branch_and_ruby(self, item: Feature, source_feature: dict, brand: dict) -> None:
        if name := source_feature.get("name"):
            item["branch"] = name
            for prefix in brand.get("branch_prefixes", []):
                item["branch"] = item["branch"].removeprefix(prefix)
            if brand.get("strip"):
                item["branch"] = item["branch"].strip()
            if suffix := brand.get("removesuffix"):
                item["branch"] = item["branch"].removesuffix(suffix)
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby
            for prefix in brand.get("ruby_prefixes", []):
                item["extras"]["branch:ja-Hira"] = item["extras"]["branch:ja-Hira"].removeprefix(prefix)

    def parse_detail_page(self, response, item, source_feature):
        # `spotDetailBean` is a JS object embedded on the detail page containing all details information
        # such as flags (services/payment) and shop data (opening hours, pharmacy options etc.).
        blob = response.xpath('//script[contains(text(), "var spotDetailBean")]/text()').get()
        if not blob:
            yield item
            return
        detail_json = parse_js_object(blob.split("var spotDetailBean = ", 1)[1])
        detail_fields = self.detail_fields(detail_json)

        if flag := detail_json["flags"].get(FLAG_CLOSED):
            if flag.get("value") == "true":
                return

        self._apply_payment_methods(item, detail_json)

        if fax := detail_fields.get(FLAG_FAX):
            if value := fax.get("value"):
                item["extras"]["fax"] = f"+81 {value}"

        if flag := detail_json["flags"].get(FLAG_TOILETS_OSTOMY):
            apply_yes_no("toilets:ostomy", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_ALCOHOL):
            apply_yes_no("alcohol", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_DUTY_FREE):
            apply_yes_no("duty_free", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_PARKING):
            apply_yes_no("parking", item, flag.get("value") == "true", apply_positive_only=False)

        self._apply_dispensing(item, detail_json, detail_fields)
        self._apply_other_services(item, detail_json)
        self._apply_opening_hours(item, detail_fields)

        yield item

    def _apply_dispensing(self, item: Feature, detail_json: dict, detail_fields: dict) -> None:
        if flag := detail_json["flags"].get(FLAG_DISPENSING):
            apply_yes_no("dispensing", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_DEDICATED_PHARMACY):
            if flag.get("value") == "true":
                apply_category(Categories.PHARMACY, item)

        if pharmacy_phone := detail_fields.get(FLAG_PHARMACY_PHONE):
            if value := pharmacy_phone.get("value"):
                item["extras"]["phone:pharmacy"] = f"+81 {value}"

        if pharmacy_fax := detail_fields.get(FLAG_PHARMACY_FAX):
            if value := pharmacy_fax.get("value"):
                item["extras"]["fax:pharmacy"] = f"+81 {value}"

    def _apply_other_services(self, item: Feature, detail_json: dict) -> None:
        if flag := detail_json["flags"].get(FLAG_UBER_EATS):
            if flag.get("value") == "true":
                item["extras"]["delivery"] = "yes"
                item["extras"]["delivery:partner"] = "Uber Eats"
                item["extras"]["delivery:partner:wikidata"] = "Q21462723"

    def _apply_opening_hours(self, item: Feature, detail_fields: dict) -> None:
        for field_code, key in ((FLAG_STORE_HOURS, "opening_hours"), (FLAG_PHARMACY_HOURS, "opening_hours:pharmacy")):
            if entry := detail_fields.get(field_code):
                if value := entry.get("value"):
                    hours = self._parse_hours(value)
                    if hours:
                        if key == "opening_hours":
                            item["opening_hours"] = hours
                        else:
                            item["extras"][key] = hours

    def _parse_hours(self, value: str) -> str | None:
        """Parse the per-day opening hours JSON into an opening_hours value.

        The source is a JSON object keyed by lowercase day names (``sunday`` ..
        ``saturday``) plus ``holiday``. A value is a list of [open, close]
        ranges, the string ``"allday"`` (open 24h), or the string ``"closed"``
        (closed that day). Weekday ranges go through the OpeningHours helper.
        """
        try:
            day_hours = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(day_hours, dict):
            return None

        oh = OpeningHours()
        for day, ranges in day_hours.items():
            if day == "holiday":
                continue
            self._add_day_hours(oh, sanitise_day(day), ranges)

        result = oh.as_opening_hours()

        if holiday_ranges := day_hours.get("holiday"):
            result += self._holiday_suffix(holiday_ranges)

        return result or None

    @staticmethod
    def _add_day_hours(oh: OpeningHours, day_code: str | None, ranges) -> None:
        if ranges == "allday":
            oh.add_range(day_code, "00:00", "24:00")
        elif ranges == "closed":
            oh.set_closed(day_code)
        elif ranges:
            for open_time, close_time in ranges:
                oh.add_range(day_code, open_time, close_time)

    @staticmethod
    def _holiday_suffix(holiday_ranges) -> str:
        if holiday_ranges == "closed":
            return "; PH off"
        return "; PH " + ",".join(f"{open_time}-{close_time}" for open_time, close_time in holiday_ranges)

    @staticmethod
    def detail_fields(detail_json: dict) -> dict[str, dict]:
        """Flatten all detailColumns sections into a code -> entry lookup."""
        fields = {}
        for section in detail_json.get("detailColumns", []):
            for entries in section.get("columns", {}).values():
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("code"):
                        fields[entry["code"]] = entry
        return fields

    def _apply_payment_methods(self, item: Feature, detail_json: dict) -> None:
        flags = detail_json["flags"]
        for code, payment in PAYMENT_METHODS.items():
            if flag := flags.get(code):
                apply_yes_no(payment, item, flag.get("value") == "true", apply_positive_only=False)


def _build_postal_lookup() -> dict[str, dict]:
    """Map each JP postcode to its region dict.

    Scans the 124K row JP postcode dataset only once at import time to avoid rescanning.
    """
    lookup = {}
    for region in postal_regions("JP"):
        lookup.setdefault(region["postal_region"], region)
    return lookup


POSTAL_LOOKUP = _build_postal_lookup()
