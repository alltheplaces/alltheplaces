from locations.storefinders.freshop import FreshopSpider


class BevMoSpiderUS(FreshopSpider):
    name = "bevmo_us"
    item_attributes = {"brand": "BevMo!", "brand_wikidata": "Q4899308"}
    api_key = "bevmo"

    def parse_item(self, item, location):
        if not location.get("has_pickup"):  # Virtual store / not a physical location
            return
        yield item
