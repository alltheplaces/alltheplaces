from locations.categories import Categories, apply_category
from locations.storefinders.storepoint import StorepointSpider


class DekaLashSpider(StorepointSpider):
    name = "deka_lash"
    item_attributes = {"brand": "Deka Lash", "brand_wikidata": "Q120505973"}
    key = "15e2b4dd23ff14"

    def parse_item(self, item, location):
        if branch := item.pop("name", "").removeprefix("Deka Lash ").strip():
            item["branch"] = branch
        if website := item.get("website"):
            if not website.startswith("http"):
                item["website"] = "https://" + website
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
