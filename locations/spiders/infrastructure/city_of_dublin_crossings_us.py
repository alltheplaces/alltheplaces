from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinCrossingsUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_crossings_us"
    item_attributes = {"operator": "City of Dublin", "operator_wikidata": "Q111367157", "state": "OH", "nsi_id": "N/A"}
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/ArcGIS"
    service_id = "Crosswalks"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GlobalID"]
        apply_category(Categories.FOOTWAY_CROSSING, item)
        if facility_id := feature.get("FacilityID"):
            item["extras"]["alt_ref"] = facility_id

        match feature["CATEGORY"]:
            case "Marking Only" | "Marking and Flat Sheet Signs":
                item["extras"]["crossing:markings"] = "yes"
                item["extras"]["crossing:signals"] = "no"
            case "Marking and Activated/Blinking Signs":
                item["extras"]["crossing:markings"] = "yes"
                item["extras"]["crossing:signals"] = "yes"
            case None:
                pass
            case _:
                self.logger.warning("Unknown crossing type: {}".format(feature["CATEGORY"]))

        if feature["Lighted"] == "Y":
            item["extras"]["lit"] = "yes"
        elif feature["Lighted"] == "N":
            item["extras"]["lit"] = "no"

        yield item
