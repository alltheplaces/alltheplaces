from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class GreaterGeelongCityCouncilBicycleParkingAUSpider(OpendatasoftExploreSpider):
    name = "greater_geelong_city_council_bicycle_parking_au"
    item_attributes = {"operator": "Greater Geelong City Council", "operator_wikidata": "Q112919122", "nsi_id": "N/A"}
    api_endpoint = "https://www.geelongdataexchange.com.au/api/explore/v2.1/"
    dataset_id = "bike-racks-greater-geelong"
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.BICYCLE_PARKING, item)
        if capacity_int := feature.get("bike_capac"):
            item["extras"]["capacity"] = str(capacity_int)
        yield item
