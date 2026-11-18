from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class AeonHokkaidoJPSpider(LocationCloudSpider):
    name = "aeon_hokkaido_jp"
    item_attributes = {"brand": "イオン", "brand_wikidata": "Q11285951"}
    api_endpoint = "https://map.aeon-hokkaido.jp/ah-store/api/proxy2/shop/list"

    BRAND_MAPPING = {
        "01": ("イオン", "Q11285951", Categories.SHOP_SUPERMARKET),
        "02": ("イオンスーパーセンター", "Q11285970", Categories.SHOP_SUPERMARKET),
        "03": ("マックスバリュ", "Q11340427", Categories.SHOP_SUPERMARKET),
        "04": ("ザ・ビッグ", "Q11306676", Categories.SHOP_SUPERMARKET),
        "05": ("フードセンター", None, Categories.SHOP_SUPERMARKET),
        "07": ("まいばすけっと", "Q11278154", Categories.SHOP_CONVENIENCE),
        "08": ("イオンモール・専門店街", "Q11286068", Categories.SHOP_MALL),
    }

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = source_feature.get("phone")
        item["website"] = source_feature.get("external_url")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")

        categories = source_feature.get("categories", [])
        cat_code = categories[0]["code"] if categories else None
        brand_info = self.BRAND_MAPPING.get(cat_code)
        if brand_info:
            brand_ja, wikidata, category = brand_info
            item["name"] = brand_ja
            item["brand"] = brand_ja
            item["brand_wikidata"] = wikidata
            item["branch"] = source_feature["name"].removeprefix(brand_ja).strip() or None
            apply_category(category, item)
        else:
            item["name"] = source_feature["name"]
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
