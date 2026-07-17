from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class GongChaSpider(StorepointSpider):
    name = "gong_cha"
    item_attributes = {"brand": "Gong Cha", "brand_wikidata": "Q5581670"}
    key = "166d1c54519253"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        if result := reverse_geocoder.get((float(item["lat"]), float(item["lon"])), mode=1, verbose=False):
            if result["cc"] == "KR":
                return  # South Korean locations are covered by the gong_cha_kr spider
        item["website"] = f"https://www.gong-cha.com/store-finder?l={location['id']}"
        item["branch"] = item.pop("name").removeprefix("Gong Cha ").removeprefix("Gong cha ")
        apply_category(Categories.CAFE, item)
        yield item
