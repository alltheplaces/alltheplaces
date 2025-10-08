from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationBasketballCourtsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_basketball_courts_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Basketball_Court_Points"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        if courts := feature.get("NUMBEROFCOURTS"):
            if courts > 1:
                apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            else:
                apply_category(Categories.LEISURE_PITCH, item)
                match feature.get("TYPE"):
                    case "Full":
                        item["extras"]["hoops"] = 2
                    case "Half":
                        item["extras"]["hoops"] = 1
                    case _:
                        self.logger.warning("Unknown court type: {}".format(feature["TYPE"]))
        apply_category({"sport": "basketball"}, item)
        yield item
