from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SeibuShinkinJPSpider(LocationCloudSpider):
    name = "seibu_shinkin_jp"
    item_attributes = {
        "brand": "西武信用金庫",
        "brand_wikidata": "Q11628905",
        "extras": {"brand:en": "Seibu Shinkin Bank"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/seibushinkin/api/proxy2/shop/list"
    additional_args = "&category=01.02"
    website_formatter = "https://pkg.navitime.co.jp/seibushinkin/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case _:
                return

        item["branch"] = (source_feature.get("name") or "").removesuffix("出張所")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        yield item
