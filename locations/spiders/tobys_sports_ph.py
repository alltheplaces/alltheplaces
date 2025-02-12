from locations.categories import Categories, apply_category
from locations.storefinders.stockinstore import StockInStoreSpider


class TobysSportsPHSpider(StockInStoreSpider):
    name = "tobys_sports_ph"
    item_attributes = {"brand": "Toby's Sports", "brand_wikidata": "Q117747741"}
    api_site_id = "10083"
    api_widget_id = "90"
    api_widget_type = "cnc"
    api_origin = "https://www.tobys.com"

    def parse_item(self, item, location):
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
