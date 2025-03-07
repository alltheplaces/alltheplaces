from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ArmyCemeteriesExplorerUSSpider(ArcGISFeatureServerSpider):
    name = "army_cemeteries_explorer_us"
    host = "ancexplorer.army.mil"
    context_path = "arcgis"
    service_id = "Data/ANC_External"
    server_type = "MapServer"
    layer_id = "0"
    # Cemeteries tuple has the cemetery (for located_in), the state, and then
    # the organisation operating each cemetery.
    cemeteries = {
        1: ("Arlington National Cemetery", "Q216344", "VA", "United States Department of the Army", "Q1328562"),
        2: ("Aberdeen Proving Ground Post Cemetery", "Q117494547", "MD", "Office of Army Cemeteries", "Q114305338"),
        4: ("Fort Moore Main Post Cemetery", "Q113111854", "GA", "Office of Army Cemeteries", "Q114305338"),
        5: ("Fort Bragg Main Post Cemetery", "Q113546385", "NC", "Office of Army Cemeteries", "Q114305338"),
        6: ("Carlisle Barracks Main Post Cemetery", "Q117516970", "PA", "Office of Army Cemeteries", "Q114305338"),
        9: ("Fort Drum Prisoner Of War Cemetery", "Q133148748", "NY", "Office of Army Cemeteries", "Q114305338"),
        10: ("Edgewood Arsenal Post Cemetery", "Q133149492", "MD", "Office of Army Cemeteries", "Q114305338"),
        11: (
            "Fort Eisenhower German and Italian Prisoner of War Cemetery",
            "Q133149865",
            "GA",
            "Office of Army Cemeteries",
            "Q114305338",
        ),
        12: ("Fort Huachuca Post Cemetery", "Q115871322", "AZ", "Office of Army Cemeteries", "Q114305338"),
        13: ("Fort Knox Post Cemetery", "Q117601183", "KY", "Office of Army Cemeteries", "Q114305338"),
        15: ("U.S. Disciplinary Barracks Cemetery", "Q5471497", "KS", "Office of Army Cemeteries", "Q114305338"),
        16: ("Fort Leonard Wood Post Cemetery", "Q117497253", "MO", "Office of Army Cemeteries", "Q114305338"),
        17: ("Camp Lewis Post Cemetery", "Q116026418", "WA", "Office of Army Cemeteries", "Q114305338"),
        19: ("Fort Meade Post Cemetery", "Q117502831", "MD", "Office of Army Cemeteries", "Q114305338"),
        21: ("Presidio of Monterey Main Post Cemetery", "Q116042041", "CA", "Office of Army Cemeteries", "Q114305338"),
        22: ("Fort Riley Post Cemetery", "Q117571183", "KS", "Office of Army Cemeteries", "Q114305338"),
        23: ("Schofield Barracks Main Post Cemetery", "Q117682792", "HI", "Office of Army Cemeteries", "Q114305338"),
        25: ("Fort Sill Post Cemetery", "Q117538802", "OK", "Office of Army Cemeteries", "Q114305338"),
        28: ("West Point Cemetery", "Q2687434", "NY", "United States Military Academy", "Q9219"),
        30: (
            "Fort Campbell Prisoner of War Post Cemetery",
            "Q133151740",
            "KY",
            "Office of Army Cemeteries",
            "Q114305338",
        ),
        31: ("Watervliet Arsenal Post Cemetery", "Q117642154", "NY", "Office of Army Cemeteries", "Q114305338"),
        32: (
            "Soldiers' and Airmen's Home National Cemetery",
            "Q7892208",
            "DC",
            "United States Department of the Army",
            "Q1328562",
        ),
        41: (
            "United States Naval Academy Cemetery",
            "Q7890788",
            "MD",
            "United States Department of the Navy",
            "Q742787",
        ),
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["cemeteryidpk"]
        item["name"] = " ".join(
            filter(
                lambda x: x.upper() != "UNKNOWN",
                filter(None, [feature["firstname"], feature["middlename"], feature["surname"]]),
            )
        )
        if not item["name"]:
            item["name"] = None
        cemetery_id = feature["cemetery_id"]
        if cemetery_id in self.cemeteries.keys():
            item["located_in"] = self.cemeteries[cemetery_id][0]
            item["located_in_wikidata"] = self.cemeteries[cemetery_id][1]
            item["state"] = self.cemeteries[cemetery_id][2]
            item["operator"] = self.cemeteries[cemetery_id][3]
            item["operator_wikidata"] = self.cemeteries[cemetery_id][4]
        else:
            self.logger.warning(
                "Unknown cemetery code `{}` with name `{}`. Perhaps a new cemetery is now included in the dataset?".format(
                    cemetery_id, feature["cemeteryname"]
                )
            )
        apply_category(Categories.GRAVE, item)
        item["extras"]["alt_ref"] = feature["gravenumber"]
        yield item
