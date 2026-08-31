from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SoilTRSpider(AgileStoreLocatorSpider):
    """
    Category 19 = "Gas Station" per the site's ASL plugin config.
    Dealer code 93982 = Soil's EPDK distributor licence number (Siyam Petrolcülük A.Ş).
    """

    name = "soil_tr"
    item_attributes = {"brand": "Soil", "brand_wikidata": "Q127395002"}
    allowed_domains = ["soil.com.tr"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("categories") != "19":
            return
        if "93982" not in (feature.get("description") or "").replace("-", ""):
            return
        item.pop("opening_hours", None)
        apply_category(Categories.FUEL_STATION, item)
        yield item
