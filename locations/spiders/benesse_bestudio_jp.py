from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class BenesseBestudioJPSpider(LocationCloudSpider):
    name = "benesse_bestudio_jp"
    item_attributes = {"brand": "ベネッセビースタジオ", "brand_wikidata": "Q817123"}
    api_endpoint = "https://school.benesse-bestudio.com/bbs/api/proxy2/shop/list"
    website_formatter = "https://school.benesse-bestudio.com/bbs/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"]
        item["phone"] = source_feature.get("phone")
        apply_category(Categories.LANGUAGE_SCHOOL, item)
        yield item
