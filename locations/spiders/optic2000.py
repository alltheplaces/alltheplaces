from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class Optic2000Spider(UberallSpider):
    name = "optic2000"
    item_attributes = {"brand": "Optic 2000", "brand_wikidata": "Q3354445"}
    key = "cnOakpSgwYPnQbwwv6ZpHtfy0PMjaK"

    def post_process_item(self, item: Feature, response, location: dict, **kwargs):
        apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
