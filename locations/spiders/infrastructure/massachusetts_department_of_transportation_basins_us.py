from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class MassachusettsDepartmentOfTransportationBasinsUSSpider(ArcGISFeatureServerSpider):
    name = "massachusetts_department_of_transportation_basins_us"
    item_attributes = {
        "operator": "Massachusetts Department of Transportation",
        "operator_wikidata": "Q2483364",
        "state": "MA",
        "nsi_id": "N/A",
    }
    host = "gis.massdot.state.ma.us"
    context_path = "arcgis"
    service_id = "Assets/Stormwater"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["AssetID"]
        apply_category(Categories.NATURAL_BASIN, item)
        match feature["BMPType"]:
            case "Bioretention Area" | "Bioretention Linear Practice" | "Wet Basin" | "Wet Linear Practice":
                item["extras"]["basin"] = "retention"
            case "Detention Basin" | "Extended Dry Detention Basin":
                item["extras"]["basin"] = "detention"
            case (
                "Infiltration Basin"
                | "Infiltration Linear Practice"
                | "Leaching Basin"
                | "Subsurface Infiltration Structure"
                | "Subsurface Infiltration System"
            ):
                item["extras"]["basin"] = "infiltration"
            case "Oil/Grit Separator":
                item["extras"]["basin"] = "settling"
            case (
                "Constructed Stormwater Wetland"
                | "Gravel Wetland"
                | "Media Filter Drain and Embankment"
                | "Other"
                | "Pavement Disconnection"
                | "Porous Pavement"
                | "Vegetated Filter Strip"
                | None
            ):
                pass
            case _:
                self.logger.warning("Unknown basin type: {}".format(feature["BMPType"]))
        yield item
