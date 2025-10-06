from typing import Iterable

from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class SkechersSpider(Where2GetItSpider):
    name = "skechers"
    item_attributes = {
        "brand_wikidata": "Q2945643",
        "brand": "Skechers",
    }
    allowed_domains = [
        "local.skechers.com",
    ]
    api_key = "8C3F989C-6D95-11E1-9DE0-BB3690553863"
    api_filter_admin_level = 1

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        yield item
