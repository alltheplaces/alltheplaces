from locations.categories import Categories
from locations.storefinders.yext import YextSpider


class Aarons(YextSpider):
    name = "aarons"
    item_attributes = {"brand": "Aaron's", "brand_wikidata": "Q10397787", "extras": Categories.SHOP_FURNITURE.value}
    api_key = "62158b834ca95fa3ef64cf0e8327c9c5"

    def parse_item(self, item, location):
        item.pop("twitter", None)
        item["extras"].pop("contact:instagram", None)
        yield item
