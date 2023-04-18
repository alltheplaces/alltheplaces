from locations.storefinders.stockinstore import StockInStoreSpider


class CoachAUNZSpider(StockInStoreSpider):
    name = "coach_au_nz"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    api_site_id = "10077"
    api_widget_id = "84"
    api_widget_type = "sis"
    api_origin = "https://coachaustralia.com"

    def parse_item(self, item, location):
        if "David Jones" in item["name"].title():
            return
        yield item
