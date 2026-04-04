from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SaizeriyaSpider(LocationCloudSpider):
    name = "saizeriya"

    item_attributes = {"brand_wikidata": "Q886564"}
    skip_auto_cc_domain = True
    api_endpoint = "https://shop.saizeriya.co.jp/sz_restaurant/api/proxy2/shop/list"
    website_formatter = "https://shop.saizeriya.co.jp/sz_restaurant/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = (
            source_feature["name"].removeprefix("サイゼリヤ ").removeprefix("Saizeriya　 ").removeprefix("Saizeriya ")
        )
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby.removeprefix("サイゼリヤ")

        apply_category(Categories.RESTAURANT, item)

        yield item
