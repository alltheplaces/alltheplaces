from locations.categories import Categories, apply_category
from locations.storefinders.storepoint import StorepointSpider


class GongChaSpider(StorepointSpider):
    name = "gong_cha"
    item_attributes = {"brand": "Gong Cha", "brand_wikidata": "Q5581670"}
    key = "166d1c54519253"

    def parse_item(self, item, location):
        item["website"] = f"https://www.gong-cha.com/store-finder?l={location['id']}"
        item["name"] = None # otherwise, branch would be the name
        item["branch"] = location["name"]
        item["extras"]["cuisine"] = "bubble_tea"
        item["extras"]["takeaway"] = "yes"
        apply_category(Categories.CAFE, item)
        yield item
