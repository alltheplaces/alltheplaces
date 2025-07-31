from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class UllaPopkenSpider(UberallSpider):
    name = "ulla_popken"
    item_attributes = {"brand": "Ulla Popken", "brand_wikidata": "Q2475146"}
    key = "HLXgKC93iNm5hhDLOOgr0r2UigmqQ5"

    def post_process_item(self, item: Feature, response, location: dict, **kwargs):
        item["branch"] = item.pop("name").split("|")[-1].lstrip()
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
