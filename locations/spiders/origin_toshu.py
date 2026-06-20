from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class OriginToshuSpider(LocationCloudSpider):
    name = "origin_toshu"
    api_endpoint = "https://shop.toshu.co.jp/toshu/api/proxy2/shop/list"
    website_formatter = "https://shop.toshu.co.jp/toshu/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        match source_feature["categories"][0]["name"]:
            case "キッチンオリジン":
                item["brand_wikidata"] = "Q92658990"
                item["branch"] = source_feature.get("name").removeprefix("キッチンオリジン ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("きっちんおりじん ")
                apply_category(Categories.FAST_FOOD, item)
            case "れんげ食堂Toshu":
                item["brand_wikidata"] = "Q92662226"
                item["branch"] = source_feature.get("name").removeprefix("れんげ食堂Toshu ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("れんげしょくどうとうしゅう ")
                apply_category(Categories.RESTAURANT, item)
            case "オリジンデリカ":
                item["brand"] = "オリジンデリカ"
                item["branch"] = source_feature.get("name").removeprefix("オリジンデリカ ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("おりじんでりか ")
                apply_category(Categories.FAST_FOOD, item)
            case "オリジン弁当":
                item["brand_wikidata"] = "Q11292632"
                item["branch"] = source_feature.get("name").removeprefix("オリジン弁当 ")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("おりじんべんとう ")
                apply_category(Categories.FAST_FOOD, item)
            case _:
                item["brand"] = source_feature["categories"][0]["name"]
                item["branch"] = source_feature.get("name")
                item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
                apply_category(Categories.RESTAURANT, item)

        yield item
