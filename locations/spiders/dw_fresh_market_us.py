from locations.storefinders.freshop import FreshopSpider


class DWFreshMarketUSSpider(FreshopSpider):
    name = "dw_fresh_market_us"
    item_attributes = {
        "brand_wikidata": "Q5203035",
        "brand": "D&W Fresh Market",
    }
    app_key = "dw_fresh_market"

    def parse_item(self, item, location):
        if "Pharmacy Phone:" in item["phone"]:
            item["phone"] = item["phone"].replace("Pharmacy Phone: ", "").split("\n")[0]
        yield item
