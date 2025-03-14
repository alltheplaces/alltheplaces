from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class GreaterGeelongCityCouncilCrossingsAUSpider(OpendatasoftExploreSpider):
    name = "greater_geelong_city_council_crossings_au"
    item_attributes = {"operator": "Greater Geelong City Council", "operator_wikidata": "Q112919122", "nsi_id": "N/A"}
    api_endpoint = "https://www.geelongdataexchange.com.au/api/explore/v2.1/"
    dataset_id = "school-crossings-city-of-greater-geelong"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["siteno"]
        item.pop("geometry", None)
        item["lat"] = feature["geo_point_2d"]["lat"]
        item["lon"] = feature["geo_point_2d"]["lon"]
        apply_category(Categories.FOOTWAY_CROSSING, item)
        item["extras"]["hazard"] = "children"
        yield item
