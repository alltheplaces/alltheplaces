from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.momentfeed import MomentFeedSpider


class VisionworksUSSpider(MomentFeedSpider):
    name = "visionworks_us"
    item_attributes = {"brand": "Visionworks", "brand_wikidata": "Q5422607"}
    api_key = "URTGGJIFYMDMAMXQ"

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        if item["name"].startswith("Visionworks ") or item["name"].startswith("Empire Visionworks "):
            item["branch"] = item["name"].removeprefix("Visionworks ").removeprefix("Empire Visionworks ")
        item.pop("name", None)
        apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
