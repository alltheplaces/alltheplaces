from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingILSpider(JSONBlobSpider):
    name = "burger_king_il"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    # API found on order's page: https://order.burgerking.co.il/branchespage/burgerking#!/branchesPage/burgerking
    start_urls = ["https://webapi.mishloha.co.il/api/Rests/GetRestaurantsInfoByChainName/burgerking"]
    locations_key = ["data", "allBranches"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["housenumber"] = feature.get("streetNum")
        item["branch"] = feature.get("restName").removeprefix("ברגר קינג ")

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.INDOOR_SEATING, item, feature.get("isEnableSitting") is True)
        apply_yes_no(Extras.TAKEAWAY, item, feature.get("enableTakeaway") is True)
        apply_yes_no(Extras.DELIVERY, item, feature.get("enableDelivery") is True)
        yield item
