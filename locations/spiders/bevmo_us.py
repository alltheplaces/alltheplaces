from locations.storefinders.freshop import FreshopSpider


class BevmoUSSpider(FreshopSpider):
    name = "bevmo_us"
    item_attributes = {"brand": "BevMo!", "brand_wikidata": "Q4899308"}
    app_key = "bevmo"

    def parse_item(self, item, location):
        if not location.get("has_pickup"):  # Virtual store / not a physical location
            return
        item.pop("name", None)
        yield item
