from locations.categories import Categories
from locations.storefinders.uberall import UberallSpider


class YvesRocherITSpider(UberallSpider):
    name = "yves_rocher_it"
    item_attributes = {
        "brand": "Yves Rocher",
        "brand_wikidata": "Q1477321",
        "extras": Categories.SHOP_BEAUTY.value,
    }
    key = "HLGRPp968JZaR0D235dXJa5fMRPHuA"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        yield item
