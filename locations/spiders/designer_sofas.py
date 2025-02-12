from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.stockist import StockistSpider


class DesignerSofasSpider(StockistSpider):
    name = "designer_sofas"
    item_attributes = {"brand": "Designer Sofas", "brand_wikidata": "Q131695219"}
    key = "u19314"

    def parse_item(self, item: Feature, location: dict):
        for custom_field in location.get("custom_fields", []):
            if custom_field["id"] == 7543:
                item["website"] = custom_field["value"]
        item["name"] = self.item_attributes["brand"]
        item["addr_full"] = merge_address_lines([item.pop("street_address"), item.get("postcode")])
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
