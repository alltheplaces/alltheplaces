import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class DaikokuyaJPSpider(LocationCloudSpider):
    name = "daikokuya_jp"
    item_attributes = {"brand": "大黒屋", "brand_wikidata": "Q11442068"}
    api_endpoint = "https://shop.e-daikoku.com/info/api/proxy2/shop/list"
    website_formatter = "https://shop.e-daikoku.com/info/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = source_feature["name"].removesuffix("大黒屋 ")
        item["extras"]["branch:en"] = source_feature.get("ruby").removesuffix("Daikokuya ")
        item["addr_full"] = re.sub(r"<\/?.*>", "", source_feature.get("address_name"))  # removes HTML

        apply_category(Categories.SHOP_PAWNBROKER, item)

        yield item
