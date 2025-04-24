from locations.categories import Categories, apply_category
from locations.storefinders.storepoint import StorepointSpider


class DonutKingAUSpider(StorepointSpider):
    name = "donut_king_au"
    item_attributes = {"brand_wikidata": "Q5296921", "brand": "Donut King"}
    key = "167209e72db19e"

    def parse_item(self, item, location):
        item["website"] = "https://donutking.com.au/"
        apply_category(Categories.FAST_FOOD, item)
        yield item
