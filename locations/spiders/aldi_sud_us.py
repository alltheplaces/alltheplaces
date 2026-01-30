from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class AldiSudUSSpider(UberallSpider):
    name = "aldi_sud_us"
    item_attributes = {"brand_wikidata": "Q41171672", "country": "US"}
    key = "LETA2YVm6txbe0b9lS297XdxDX4qVQ"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        
        apply_category(Categories.SHOP_SUPERMARKET, item)
        
        yield item
