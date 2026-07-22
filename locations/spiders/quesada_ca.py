from locations.categories import Categories, apply_category
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class QuesadaCASpider(SuperStoreFinderSpider):
    name = "quesada_ca"
    item_attributes = {"brand": "Quesada", "brand_wikidata": "Q66070360"}
    allowed_domains = ["locations.quesada.ca"]

    def parse_item(self, item, location):
        item.pop("email", None)
        item.pop("website", None)
        if name := item.pop("name", None):
            item["branch"] = name.removeprefix("Quesada - ")
        apply_category(Categories.FAST_FOOD, item)
        yield item
