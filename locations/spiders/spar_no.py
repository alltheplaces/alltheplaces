from locations.categories import Categories, apply_category
from locations.storefinders.sylinder import SylinderSpider


class SparNOSpider(SylinderSpider):
    name = "spar_no"
    app_key = "1210"
    base_url = "https://spar.no/Finn-butikk/"

    def parse_item(self, item, location, **kwargs):
        if "EUROSPAR" in location["storeDetails"].get("storeName", "").upper():
            item["brand"] = "Eurospar"
            item["brand_wikidata"] = "Q12309283"
        else:
            item["brand"] = "Spar"
            item["brand_wikidata"] = "Q610492"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
