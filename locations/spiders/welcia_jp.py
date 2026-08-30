from collections.abc import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class WelciaJPSpider(LocationCloudSpider):
    name = "welcia_jp"
    item_attributes = {
        "brand": "ウエルシア薬局",
        "brand_wikidata": "Q11288687",
    }
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

        match source_feature["categories"][0]["code"]:
            case "01":  # ウエルシア
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("ウエルシア").removeprefix("薬局")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ウエルシア").removeprefix("薬局")
            case "02":  # ハックドラッグ (HAC drug)
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("ハックドラッグ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ハックドラッグ")
            case "03":  # ダックス
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("薬局ダックス").removeprefix("ダックス")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ダックス")
            case "04":  # ハッピードラッグ
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11368084"
                if name := source_feature.get("name"):
                    item["branch"] = (
                        name.removeprefix("ハッピー・ドラッグ")
                        .removeprefix("ハッピー調剤薬局")
                        .removeprefix("ハッピードラッグ")
                    )
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ハッピードラッグ")
            case "05":  # カラースタジオ
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("カラースタジオ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("カラースタジオ")
            case "06":  # 金光薬品
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11646466"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("金光薬品").removeprefix("金光薬局")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("カネミツヤッキョク")
            case "07":  # マサヤ
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("マサヤ ")
            case "08":  # よどやドラッグ
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11281187"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("よどやドラッグ")
            case "09":  # マルエドラッグ
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11298666"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("マルエドラッグ").removeprefix("マルエ薬局")
            case "10":  # アリエールLAUNDRY PRO
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                apply_category(Categories.SHOP_COUNTRY_STORE, item)
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("アリエールLAUNDRY PRO ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("アリエールランドリープロ")
            case "11":  # ププレひまわり
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q119871972"
                if name := source_feature.get("name"):
                    item["branch"] = (
                        name.removeprefix("スーパードラッグひまわり")
                        .removeprefix("フード＆ドラッグひまわり")
                        .removeprefix("ププレひまわり薬局")
                        .removeprefix("ププレひまわり")
                    )
            case "12":  # NARCIS
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                apply_category(Categories.SHOP_COSMETICS, item)
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("NARCIS")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ナルシス")
            case "13":  # コクミン
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11301923"
                if name := source_feature.get("name"):
                    item["branch"] = (
                        name.removeprefix("KoKuMiN")
                        .removeprefix("コクミンドラッグ")
                        .removeprefix("コクミン薬局")
                        .removeprefix("コクミン")
                        .removeprefix("FamilyMart+コクミンドラッグ")
                        .removeprefix("AIRPORT＋DRUG")
                        .removeprefix("AIRPORT+DRUG ")
                        .removeprefix("CityDrug ")
                        .removeprefix("KeiyoDrug ")
                    )
            case "14":  # アルビオンドレッサー
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("アルビオンドレッサー")
            case "15":  # アトリエアルビオン
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("アトリエアルビオン")
            case "16":  # ふく薬品
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q119380891"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("ふく薬品").removeprefix("ふく薬局").strip()
            case "18":  # Zoomore
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                apply_category(Categories.SHOP_PET, item)
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("Zoomore")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ズーモア")
            case "19":  # コスメテリア
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = ""
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("コスメテリア")
            case "20":  # とをしや薬局
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11273556"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("とをしや").removesuffix("とをしや薬局")
            case "21":  # ウェルパーク
                item["brand"] = source_feature["categories"][0]["name"]
                item["brand_wikidata"] = "Q11288610"
                if name := source_feature.get("name"):
                    item["branch"] = name.removeprefix("ウェルパーク").removeprefix("薬局")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("ウェルパーク").removeprefix("薬局")
            case _:
                return

        if branch := item.get("branch"):
            item["branch"] = branch.removesuffix(" (調剤薬局)").removesuffix("(調剤薬局)").strip()

        yield item

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
