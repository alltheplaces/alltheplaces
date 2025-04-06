from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class NewYorkCityDepartmentOfSanitationWasteBasketsUSSpider(SocrataSpider):
    name = "new_york_city_department_of_sanitation_waste_baskets_us"
    item_attributes = {"operator": "New York City Department of Sanitation", "operator_wikidata": "Q8354833", "state": "NY"}
    host = "data.cityofnewyork.us"
    resource_id = "8znf-7b2c"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["ownertype"] != "D":
            # D = DSNY-owned, B = BID-owned, O = Other, P = Privately owned
            return
        item["ref"] = feature["basketid"]
        apply_category(Categories.WASTE_BASKET, item)
        yield item
