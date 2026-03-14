from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class AldiSudIESpider(UberallSpider):
    name = "aldi_sud_ie"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171672"}
    key = "lS2g9eY7aREuErMGkEiNnvTRoO6jQM"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["phone"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
