from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SuperHotelJPSpider(LocationCloudSpider):
    name = "super_hotel_jp"
    item_attributes = {"brand_wikidata": "Q11313858"}
    api_endpoint = "https://pkg.navitime.co.jp/superhotel-map/api/proxy2/shop/list"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"].removeprefix("スーパーホテル")
        if phone := source_feature.get("phone"):
            item["phone"] = phone
        item["website"] = item["extras"]["website:ja"] = source_feature["external_url"]
        slug = source_feature["external_url"].split("/")[-2]
        item["extras"]["website:en"] = f"https://www.superhoteljapan.com/en/s-hotels/{slug}/"
        item["extras"]["website:kr"] = f"https://www.superhoteljapan.com/kr/s-hotels/{slug}/"
        item["extras"]["website:cn"] = f"https://www.superhoteljapan.com/cn/s-hotels/{slug}/"

        apply_category(Categories.HOTEL, item)

        yield item
