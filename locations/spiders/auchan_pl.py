from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider

# Types stored at https://api.auchan.com/corp/cms/v4/pl/template/store-types?lang=pl (accessible only from website)
SUB_BRANDS_MAPPING = {
    "126": ("Auchan Hiper", "Q758603", Categories.SHOP_SUPERMARKET),
    "129": ("Auchan Super", "Q758603", Categories.SHOP_SUPERMARKET),
    "132": ("Auchan Moje", "Q758603", Categories.SHOP_SUPERMARKET),
    "10968": ("Auchan Easy", "Q758603", Categories.SHOP_CONVENIENCE),
    "58596": ("Auchan Go", "Q758603", Categories.SHOP_CONVENIENCE),
}

DEFAULT_BRAND = ("Auchan", "Q758603", Categories.SHOP_SUPERMARKET)

# TODO: services at https://api.auchan.com/corp/cms/v4/pl/template/store-services?lang=pl (accessible only from website)


class AuchanPLSpider(WoosmapSpider):
    name = "auchan_pl"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}
    key = "woos-2f2a4a05-1e11-3393-a97a-bf416ff688ac"
    origin = "https://www.auchan.pl"

    def parse_item(self, item, feature, **kwargs):
        item["addr_full"] = item.pop("street_address")
        if item.get("website"):
            item["website"] = urljoin(self.origin, item["website"])

        store_types = feature.get("properties", {}).get("types", [])

        if not store_types:
            self.apply_brand(item, DEFAULT_BRAND)
        else:
            store_type = store_types[0]
            brand = SUB_BRANDS_MAPPING.get(store_type, DEFAULT_BRAND)

            if brand == DEFAULT_BRAND:
                self.crawler.stats.inc_value(f"atp/auchan_pl/unknown_category/{store_type}")

            self.apply_brand(item, brand)

        yield item

    def apply_brand(self, item, brand):
        item["brand"] = brand[0]
        item["brand_wikidata"] = brand[1]
        apply_category(brand[2], item)
