from collections.abc import Iterable

from locations.categories import Categories, apply_category
from locations.geo import postal_regions
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


class WelciaJPSpider(LocationCloudSpider):
    name = "welcia_jp"
    item_attributes = {"extras": {"shop": "chemist"}}
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

    # TODO: update LocationCloudSpider
    # optional fetching detail page to fill opening hours etc.
    #
    # draft:
    # if parse_detail_page defined
    #   parse() yield new Request for detailPage with callback parse_detail_page()
    #     parse_detail_page() adds extra tags from detail page
    #
    # note: some info is written in natural language
    def parse_detail_page(self):
        # TODO: check `seims_jp.py` for detailed pharmacy-related tags
        pass


def _build_postal_lookup() -> dict[str, dict]:
    """Map each JP postcode to its region dict.

    Scans the 124K row JP postcode dataset only once at import time to avoid rescanning.
    """
    lookup = {}
    for region in postal_regions("JP"):
        lookup.setdefault(region["postal_region"], region)
    return lookup


POSTAL_LOOKUP = _build_postal_lookup()
