from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class DesignerSofasGBSpider(StockistSpider):
    name = "designer_sofas_gb"
    item_attributes = {"brand": "Designer Sofas", "brand_wikidata": "Q131695219"}
    key = "u19314"

    def parse_item(self, item: Feature, location: dict):
        for custom_field in location.get("custom_fields", []):
            if custom_field["id"] == 7543:
                item["website"] = custom_field["value"]
        item["name"] = self.item_attributes["brand"]
        if addr := item.pop("street_address"):
            if postcode := item.get("postcode"):
                addr += ", " + postcode
            item["addr_full"] = addr
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
