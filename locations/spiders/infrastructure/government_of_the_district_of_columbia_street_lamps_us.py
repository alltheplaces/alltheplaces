from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GovernmentOfTheDistrictOfColumbiaStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "government_of_the_district_of_columbia_street_lamps_us"
    item_attributes = {
        "operator": "Government of the District of Columbia",
        "operator_wikidata": "Q16152667",
        "state": "DC",
    }
    host = "maps2.dcgis.dc.gov"
    context_path = "dcgis"
    service_id = "DCGIS_DATA/Transportation_Signs_Signals_Lights_WebMercator"
    server_type = "MapServer"
    layer_id = "90"
    # There is no robots.txt nor use of HTTP 429 however it appears that the
    # server is configured or behind a network configured to drop connection
    # attempts if they occur at whatever has been decided to be too fast.
    custom_settings = {"DOWNLOAD_DELAY": 30}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FACILITYID"]
        if feature.get("HOUSENO") != "0":
            item["housenumber"] = feature["HOUSENO"]
        else:
            item.pop("housenumber", None)
        apply_category(Categories.STREET_LAMP, item)
        if height_ft := feature.get("POLEHEIGHT_DESC"):
            height_ft = height_ft.removesuffix(" ft")
            item["extras"]["height"] = f"{height_ft}'"
        if material := feature.get("POLECOMPOSITION_DESC"):
            match material:
                case "Aluminum":
                    item["extras"]["material"] = "aluminium"
                case "Cast Iron":
                    item["extras"]["material"] = "cast_iron"
                case "Composite":
                    item["extras"]["material"] = "composite"
                case "Concrete":
                    item["extras"]["material"] = "concrete"
                case "Metal":
                    item["extras"]["material"] = "metal"
                case "Steel":
                    item["extras"]["material"] = "steel"
                case "Wood":
                    item["extras"]["material"] = "wood"
                case "N/A":
                    pass
                case _:
                    self.logger.warning("Unknown pole material: {}".format(feature["POLECOMPOSITION_DESC"]))
        yield item
