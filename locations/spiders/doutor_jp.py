import json
from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

BRANDS = {
    "ドトールコーヒーショップ": ("Q11322732", Categories.CAFE),
    "ドトールキッチン": (None, Categories.FAST_FOOD),
    "ドトールスタンド": (None, Categories.CAFE),
    "ドトール パークカフェ": (None, Categories.CAFE),
    "ドトール珈琲農園": (None, Categories.CAFE),
    "ドトール珈琲店": (None, Categories.CAFE),
    "エクセルシオール カフェ": ("Q11289828", Categories.CAFE),
    "カフェ レクセル": (None, Categories.CAFE),
    "カフェ コロラド": ("Q141274050", Categories.CAFE),
    "神乃珈琲": (None, Categories.CAFE),
    "梟書茶房": (None, Categories.CAFE),
    "コッペ田島": (None, Categories.SHOP_BAKERY),
    "ラスールオーバカナル": (None, Categories.RESTAURANT),
    "オーバカナル": (None, Categories.RESTAURANT),
    "ル サロン ド ニナス": (None, Categories.CAFE),
    "ニナス パリ": (None, Categories.CAFE),
    "カフェラミル": (None, Categories.CAFE),
    "マウカメドウズ": (None, Categories.CAFE),
}
NSI_BRANDS = {"ドトールコーヒーショップ", "エクセルシオール カフェ"}


class DoutorJPSpider(LocationCloudSpider):
    name = "doutor_jp"
    api_endpoint = "https://shop.doutor.co.jp/doutor/api/proxy2/shop/list"
    website_formatter = "https://shop.doutor.co.jp/doutor/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        name = source_feature["name"]
        prefix, (brand_wikidata, category) = next((p, b) for p, b in BRANDS.items() if name.startswith(p))

        if prefix not in NSI_BRANDS:
            item["brand"] = prefix
        if brand_wikidata:
            item["brand_wikidata"] = brand_wikidata
        item["branch"] = name.removeprefix(prefix).lstrip()
        item["phone"] = f"+81 {source_feature['phone']}"

        apply_category(category, item)
        if category == Categories.CAFE:
            cuisine = item["extras"].get("cuisine")
            item["extras"]["cuisine"] = f"coffee_shop;{cuisine}" if cuisine else "coffee_shop"

        yield item

    def parse_detail_page(self, response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]
        flags = {flag["label"]: flag["value"] == "true" for flag in detail["flags"].values()}

        apply_yes_no(Extras.WIFI, item, flags["FREE Wi-Fi"])
        if flags["FREE Wi-Fi"]:
            item["extras"]["internet_access:fee"] = "no"
        apply_yes_no("socket:nema_1_15", item, flags["コンセント"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, flags["ドライブスルー"])

        if flags["全席禁煙"]:
            item["extras"]["smoking"] = "no"
        elif flags["完全分煙"]:
            item["extras"]["smoking"] = "isolated"

        if flags["カフェインレスコーヒー"]:
            item["extras"]["drink:coffee:decaf"] = "yes"

        partners = []
        if flags["出前館対応"]:
            partners.append(("出前館", "Q11395551"))
        if flags["Uber Eats対応"]:
            partners.append(("Uber Eats", "Q21462723"))
        if partners:
            apply_yes_no(Extras.DELIVERY, item, True)
            item["extras"]["delivery:partner"] = ";".join(partner[0] for partner in partners)
            item["extras"]["delivery:partner:wikidata"] = ";".join(partner[1] for partner in partners)

        cuisines = []
        if flags["パスタ"]:
            cuisines.append("pasta")
        if flags["ソフトクリーム"]:
            cuisines.append("ice_cream")
        if flags["ホットサンド"] or flags["店舗限定サンド"]:
            cuisines.append("sandwich")
        if any(
            flags[label]
            for label in (
                "モーニングセット",
                "モーニング（全日）",
                "モーニング（平日のみ）",
                "モーニング（平日・土）",
                "モーニング（土日のみ）",
            )
        ):
            cuisines.append("breakfast")
        if cuisines:
            item["extras"]["cuisine"] = ";".join(cuisines)

        yield item
