from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockinstore import StockInStoreSpider


class KidstuffAUSpider(StockInStoreSpider):
    name = "kidstuff_au"
    item_attributes = {"brand": "Kidstuff", "brand_wikidata": "Q117746407"}
    api_site_id = "10041"
    api_widget_id = "48"
    api_origin = "https://www.kidstuff.com.au"

    def parse_item(self, item: Feature, location: dict):
        item["website"] = urljoin(self.api_origin, item["website"])
        item["branch"] = item.pop("name").removeprefix("Kidstuff ")
        apply_category(Categories.SHOP_TOYS, item)
        yield item
