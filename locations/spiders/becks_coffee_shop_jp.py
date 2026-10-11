from typing import Iterable

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider, parse_opening_hours


class BecksCoffeeShopJPSpider(LocationCloudSpider):
    name = "becks_coffee_shop_jp"
    item_attributes = {"brand": "BECK'S COFFEE SHOP", "brand_wikidata": "Q11191008"}
    api_endpoint = "https://shop.jr-cross.co.jp/eki/api/proxy2/shop/list"
    additional_args = "&word=BECK%27S+COFFEE+SHOP&search-target=name.search_word.c_d85&add=detail&device=pc"
    website_formatter = "https://shop.jr-cross.co.jp/eki/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"].removeprefix("BECK'S COFFEE SHOP").strip()
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Kana"] = ruby.removeprefix("ベックスコーヒーショップ").strip()
        if phone := source_feature.get("phone"):
            item["phone"] = f"+81 {phone}"

        details = (source_feature.get("details") or [{}])[0]
        texts = {t["label"]: t["value"] for t in details.get("texts", [])}
        flags = {f["label"]: f["value"] for f in details.get("flags", [])}

        if flags.get("閉店"):
            return

        item["opening_hours"] = parse_opening_hours(texts)

        apply_yes_no(PaymentMethods.SUICA, item, flags.get("Suica決済"))
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, flags.get("クレジット決済"))
        apply_yes_no(Extras.WIFI, item, flags.get("WiFi"))
        apply_yes_no(Extras.WHEELCHAIR, item, flags.get("車いす入店可"))

        yield item
