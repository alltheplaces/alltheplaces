from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider

# Types stored at https://api.auchan.com/corp/cms/v4/pl/template/store-types?lang=pl (accessible only from website)
CATEGORY_MAPPING = {
    "126": Categories.SHOP_SUPERMARKET,  # Auchan Hiper
    "129": Categories.SHOP_SUPERMARKET,  # Auchan Super
    "132": Categories.SHOP_SUPERMARKET,  # Auchan Moje
    "10968": Categories.SHOP_CONVENIENCE,  # Auchan Easy
    "58596": Categories.SHOP_CONVENIENCE,  # Auchan Go
}

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
            # Default to supermarket if no specific type is given
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            store_type = store_types[0]
            if category := CATEGORY_MAPPING.get(store_type):
                apply_category(category, item)
            else:
                self.crawler.stats.inc_value(f"atp/auchan_pl/unknown_category/{store_type}")

        yield item
