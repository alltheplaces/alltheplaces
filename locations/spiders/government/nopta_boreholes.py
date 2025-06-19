from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NoptaBoreholesSpider(ArcGISFeatureServerSpider):
    name = "nopta_boreholes"
    allowed_domains = ["services.neats.nopta.gov.au", "arcgis.nopta.gov.au"]
    start_urls = [
        "https://services.neats.nopta.gov.au/odata/v1/public/nopims/well/PublicNopimsWells?$orderby=Kick_Off_Date desc&$top=100000&$skip=0&$filter=contains(Well,'')"
    ]

    host = "arcgis.nopta.gov.au"
    context_path = "arcgis"
    service_id = "Public/Petroleum_Wells"
    server_type = "FeatureServer"
    layer_id = "0"

    _wells: dict = {}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], callback=self.parse_odata_well_list)

    def parse_odata_well_list(self, response: Response) -> Iterable[JsonRequest]:
        for well in response.json()["value"]:
            self._wells[well["Borehole_ID"]] = self.extract_odata_well(well)
        yield JsonRequest(
            url=f"https://{self.host}/{self.context_path}/rest/services/{self.service_id}/{self.server_type}/{self.layer_id}?f=json",
            callback=self.parse_layer_details,
        )

    def extract_odata_well(self, feature: dict) -> Feature:
        item = Feature()
        item["ref"] = feature["Borehole_ID"]
        item["name"] = feature["Borehole"]
        if operator := feature["Borehole_Operator"]:
            item["operator"] = operator
        elif operator := feature["Well_Operator"]:
            item["operator"] = operator
        if state := feature["State"]:
            if state != "Outside of Australia":
                item["state"] = state

        if feature["Borehole_Status"] in ["Abandoned", "Plugged and Abandoned"]:
            item["extras"]["abandoned:man_made"] = "petroleum_well"
        elif feature["Borehole_Status"] == "Suspended":
            apply_category(Categories.PETROLEUM_WELL, item)
            item["extras"]["disused"] = "yes"
        else:
            apply_category(Categories.PETROLEUM_WELL, item)

        item["extras"]["alt_ref"] = str(feature["NoptaBoreholeId"])
        item["extras"]["ref:uwi"] = feature["Well_ID"]
        item["extras"]["ref:ubhi"] = feature["Borehole_ID"]

        if start_date := feature["Kick_Off_Date"]:
            item["extras"]["start_date"] = start_date.split("T", 1)[0]
        if end_date := feature["Rig_Release_Date"]:
            item["extras"]["end_date"] = end_date.split("T", 1)[0]

        if depth_m := feature["Drillers_TD_m"]:
            item["extras"]["depth"] = depth_m

        return item

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        ubhi = feature["Ubhi"]
        if ubhi not in self._wells.keys():
            raise ValueError(
                "Borehole {} present in ArcGIS FeatureServer layer, but not present in odata API response for list of wells. Borehole ignored.".format(
                    ubhi
                )
            )
        odata_feature = self._wells[ubhi]
        odata_feature["lat"] = feature["Latitude"]
        odata_feature["lon"] = feature["Longitude"]

        if "man_made" in odata_feature["extras"]:
            odata_feature["extras"].pop("man_made")
        match feature["Type"]:
            case "Mineral or Coal" | "Stratigraphic":
                apply_category(Categories.BOREHOLE, odata_feature)
            case "Petroleum":
                apply_category(Categories.PETROLEUM_WELL, odata_feature)
            case "Greenhouse Gas":
                apply_category(Categories.BOREHOLE, odata_feature)
                odata_feature["extras"]["direction"] = "injection"
                odata_feature["extras"]["substance"] = "carbon_dioxide"
            case "Groundwater":
                apply_category(Categories.WATER_WELL, odata_feature)
            case _:
                apply_category(Categories.BOREHOLE, odata_feature)
                if feature["Type"]:
                    self.logger.warning("Unknown borehole type: {}".format(feature["Type"]))
        if "abandoned:man_made" in odata_feature["extras"]:
            odata_feature["extras"]["abandoned:man_made"] = odata_feature["extras"].pop("man_made")

        odata_feature["extras"]["@source"] = response.url + ";" + self.start_urls[0]

        yield odata_feature
