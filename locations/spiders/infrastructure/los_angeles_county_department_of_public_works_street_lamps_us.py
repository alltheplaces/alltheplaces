from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LosAngelesCountyDepartmentOfPublicWorksStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "los_angeles_county_department_of_public_works_street_lamps_us"
    item_attributes = {
        "operator": "Los Angeles County Department of Public Works",
        "operator_wikidata": "Q6682081",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "dpw.gis.lacounty.gov"
    context_path = "dpw"
    service_id = "PW_Open_Data"
    server_type = "MapServer"
    layer_id = "5"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.STREET_LAMP, item)
        if sce_id := feature.get("SCE_POL_I"):
            item["extras"]["alt_ref"] = sce_id
        match feature["POLE_TYPE"]:
            case "C":
                item["extras"]["material"] = "concrete"
            case "F":
                item["extras"]["material"] = "fiberglass"
            case "S":
                item["extras"]["material"] = "steel"
            case "W":
                item["extras"]["material"] = "wood"
            case "HSL" | "SUP" | None:
                pass
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["POLE_TYPE"]))
        yield item
