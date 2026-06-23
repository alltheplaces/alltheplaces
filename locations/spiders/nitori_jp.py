from typing import Iterable

from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class NitoriJPSpider(LocationCloudSpider):
    name = "nitori_jp"
    item_attributes = {
        "brand": "ニトリ",
        "brand_wikidata": "Q10801453",
    }
    api_endpoint = "https://shop.nitori-net.jp/nitori/api/proxy2/shop/list"
    website_formatter = "https://shop.nitori-net.jp/nitori/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] == "03":
            return  # skip logistics centers
        
        item["branch"] = source_feature.get("name", "")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby", "")
        item["phone"] = f"+81 {source_feature.get('phone', '')}"

        yield item
