from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider


class SisleySpider(WoosmapSpider):
    name = "sisley"
    item_attributes = {"brand": "Sisley", "brand_wikidata": "Q12054325"}
    key = "woos-2aa481bb-5ce8-345c-98a3-c0868e27727f"
    origin = "https://www.sisley.com"

    def parse_item(self, item, feature, **kwargs):
        item.pop("website")
        item["branch"] = item.pop("name").replace("Sisley ", "")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
