import re

from requests_cache import Iterable

from locations.categories import Categories, apply_category
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider, Feature, TextResponse


class HipermaxiBOSpider(AgileStoreLocatorSpider):
    name = "hipermaxi_bo"
    item_attributes = {"brand_wikidata": "Q81968262", "brand": "Hipermaxi"}
    allowed_domains = ["informacion.hipermaxi.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(
            r"^(MINI DRUGSTORE|DRUGSTORE|FARMACIA|HIPERMAXI) ", "", item.pop("name"), flags=re.IGNORECASE
        )
        if feature.get("marker_id") == "153":
            apply_category(Categories.PHARMACY, item)
            item["nsi_id"] = "N/A"
        elif feature.get("marker_id") == "152":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        item["website"] = "https://www.hipermaxi.com/sucursales"
        yield item
