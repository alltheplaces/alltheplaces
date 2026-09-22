import re
from typing import Iterable
from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.david_jones_au_nz import DavidJonesAUNZSpider
from locations.spiders.myer_au import MyerAUSpider
from locations.storefinders.stockinstore import StockInStoreSpider

FOREVER_NEW_SHARED_ATTRIBUTES = {"brand": "Forever New", "brand_wikidata": "Q119221929"}


class ForeverNewAUNZSpider(StockInStoreSpider):
    name = "forever_new_au_nz"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    api_site_id = "10400"
    api_widget_id = "404"
    api_widget_type = "storelocator"
    api_origin = "https://www.forevernew.com.au"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        name = item.pop("name")
        item["branch"] = re.sub(
            r"^Forever New(?: and Forever New Curve| Curve)?(?: at)?\s*[-–]?\s*(?:Myer|David Jones)?\s*[-–]?\s*",
            "",
            name,
        )
        if name.startswith("Forever New Curve"):
            item["branch"] += " (Curve)"
        if "Myer" in name:
            item["located_in"] = MyerAUSpider.item_attributes["brand"]
            item["located_in_wikidata"] = MyerAUSpider.item_attributes["brand_wikidata"]
        elif "David Jones" in name:
            item["located_in"] = DavidJonesAUNZSpider.item_attributes["brand"]
            item["located_in_wikidata"] = DavidJonesAUNZSpider.item_attributes["brand_wikidata"]
        if page_url := location.get("store_locator_page_url"):
            item["website"] = urljoin(self.api_origin, page_url)
        else:
            item["website"] = None
        if item.get("email") == "customers@forevernew.com.au":
            item["email"] = None
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
