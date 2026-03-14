from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class AldiSudDESpider(UberallSpider):
    name = "aldi_sud_de"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171672"}
    key = "gqNws2nRfBBlQJS9UrA8zV9txngvET"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["phone"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
