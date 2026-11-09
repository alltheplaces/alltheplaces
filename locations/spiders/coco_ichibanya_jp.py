from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class CocoIchibanyaJPSpider(GogaStoreLocatorSpider):
    name = "coco_ichibanya_jp"
    item_attributes = {
        "brand_wikidata": "Q5986105",
    }
    start_urls = ["https://tenpo.ichibanya.co.jp/api/point"]
    # The API requires a trailing slash after the geohash
    geohashes = ["w/", "xj/", "xn/", "xp/", "z/"]
    website_formatter = "https://tenpo.ichibanya.co.jp/map/{}/"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["extras"]["addr:province"] = source_feature.get("住所(都道府県)")
        item["city"] = source_feature.get("住所(市町村区郡)")
        item["street_address"] = source_feature.get("住所(その他)")
        item["postcode"] = source_feature.get("郵便番号")
        item["branch"] = source_feature["name"]
        item["extras"]["branch:jp"] = source_feature["name"]
        item["extras"]["branch:en"] = source_feature.get("店舗名（英語）")
        item["phone"] = None
        if (phone := source_feature.get("TEL", "-")) != "-":
            item["phone"] = f"+81 {phone}"
        if (capacity := source_feature.get("座席数", "0")) != "0":
            item["extras"]["capacity"] = capacity
        if source_feature.get("24時間営業") == "1":
            item["opening_hours"] = "24/7"
        apply_yes_no(Extras.DRIVE_THROUGH, item, source_feature.get("ドライブスルー") == "1")
        apply_yes_no(Extras.DELIVERY, item, source_feature.get("宅配") == "1")
        if source_feature.get("カウンターのみ（座席）") == "1":
            item["extras"]["indoor_seating"] = "bar_table"
        if source_feature.get("駐車場") == "1":
            item["extras"]["parking"] = "yes"
        if source_feature.get("お子様メニュー") == "1":
            item["extras"]["child"] = "yes"
        if source_feature.get("ベビーフード") == "1":
            item["extras"]["baby"] = "yes"
        if (order_url := source_feature.get("モバイルオーダー", "")).startswith("http"):
            item["extras"]["website:orders"] = order_url
        item["name"] = None

        apply_category(Categories.RESTAURANT, item)

        yield item
