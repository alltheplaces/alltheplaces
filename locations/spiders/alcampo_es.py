from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider


class AlcampoESSpider(WoosmapSpider):
    name = "alcampo_es"
    item_attributes = {"brand": "Alcampo", "brand_wikidata": "Q2832081"}
    key = "woos-761853c3-bb35-3187-98a8-91b1853d08d7"
    origin = "https://www.alcampo.es/"

    def parse_item(self, item, feature, **kwargs):
        item.pop("website")
        if feature["properties"]["user_properties"]["isGAS"]:
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
