from typing import AsyncIterator, Iterable

from locations.categories import Categories, Extras, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class SoederCHSpider(StoremapperSpider):
    name = "soeder_ch"
    company_id = "16023-r6PfOZv3OfbeGfgX"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        # Soeder has a few flagship stores under their own brand, but most stores
        # in their storefinder page are merely _selling_ Soeder products. Many of
        # these are concept stores or independent small boutiques that are not
        # listed anywhere else; having these stores in ATP seems useful.
        #
        # https://wiki.openstreetmap.org/wiki/Key:brand#Brand_of_feature_vs_brands_on_sale_/_service_/_repair_/_rental
        # https://taginfo.openstreetmap.org/keys/brand:sales#values
        # https://taginfo.openstreetmap.org/keys/brand:sales:wikidata#values
        name = item.get("name", "")
        if name == "Soeder Store":
            item["brand"] = "Soeder"
            item["brand_wikidata"] = "Q111722324"
            # Category comes from NSI.
            yield item
            return

        extras = item.setdefault("extras", {})
        extras["brand:sales"] = "Soeder"
        extras["brand:sales:wikidata"] = "Q111722324"
        name_lower = name.lower()
        if "hotel" in name_lower:
            apply_category(Categories.HOTEL, item)
        elif "micasa" in name_lower:
            apply_category(Categories.SHOP_FURNITURE, item)
        else:
            apply_category(Categories.GENERIC_SHOP, item)
        yield item
