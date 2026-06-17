from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SeijoishiiJPSpider(LocationCloudSpider):
    name = "seijoishii_jp"
    item_attributes = {"brand": "成城石井", "brand_wikidata": "Q11495410"}
    api_endpoint = "https://shop.seijoishii.com/seijoishii/api/proxy2/shop/list"
    website_formatter = "https://shop.seijoishii.com/seijoishii/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] != "03":
            return  # skip other types

        item["branch"] = source_feature["name"]
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
        item["phone"] = f"+81 {source_feature['phone']}"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
