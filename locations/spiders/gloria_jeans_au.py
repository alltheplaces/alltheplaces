from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.storepoint import StorepointSpider


class GloriaJeansAUSpider(StorepointSpider):
    name = "gloria_jeans_au"
    item_attributes = {"brand": "Gloria Jean's", "brand_wikidata": "Q2666365"}
    key = "1672034abefd98"

    def parse_item(self, item, location):
        if "gloria jeans vans" in location.get("tags"):
            # Not a fixed location. Is a franchise mobile coffee van business.
            return
        item["ref"] = location["description"]
        item["branch"] = item.pop("name").removeprefix("Gloria Jean's ").removeprefix("Gloria Jeans ")
        apply_category(Categories.COFFEE_SHOP, item)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "drive thru" in location.get("tags"))
        yield item
