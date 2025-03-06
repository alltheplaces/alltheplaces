from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GreaterMetropolitanCemeteriesTrustGravesAUSpider(ArcGISFeatureServerSpider):
    name = "greater_metropolitan_cemeteries_trust_graves_au"
    item_attributes = {"operator": "The Greater Metropolitan Cemeteries Trust", "operator_wikidata": "Q133070428", "state": "VIC"}
    host = "maps.gmct.com.au"
    context_path = "server"
    service_id = "Public_Map250924_MIL1"
    server_type = "MapServer"
    layer_id = "17"
    cemeteries = {
        "ACC": ("Andersons Creek Cemetery", "Q133071050"),
        "AMP": ("Altona Memorial Park", "Q48779318"),
        "BUR": ("Burwood Cemetery", "Q18922790"),
        "COB": ("Coburg Pine Ridge Cemetery", "Q5139019"),
        "EMC": ("Emerald Cemetery", "Q133074102"),
        "FGC": ("Footscray General Cemetery", "Q117797991"),
        "FMP": ("Fawkner Memorial Park", "Q5438753"),
        "HVC": ("Healesville Cemetery", "Q133074195"),
        "KEL": ("Keilor Cemetery", "Q133075121"),
        "LLC": ("Lilydale Lawn Cemetery", "Q133074312"),
        "LMP": ("Lilydale Memorial Park", "Q118800701"),
        "NMP": ("Northern Memorial Park", "Q133070786"),
        "NOC": ("Northcote Cemetery", "Q128798876"),
        "PRE": ("Preston Cemetery", "Q115516595"),
        "TEM": ("Templestowe Cemetery", "Q130477090"),
        "TRU": ("Truganina Cemetery", "Q133075215"),
        "WER": ("Werribee Cemetery", "Q133075394"),
        "WIL": ("Williamstown Cemetery", "Q28147798"),
        "YGC": ("Yarra Glen Cemetery", "Q133074518"),
    }


    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GISLocation"]
        item["name"] = feature["names"]
        cemetery_code = item["ref"][0:3]
        if cemetery_code in self.cemeteries.keys():
            item["located_in"] = self.cemeteries[cemetery_code][0]
            item["located_in_wikidata"] = self.cemeteries[cemetery_code][1]
        else:
            self.logger.warning("Unknown cemetery code `{}`. Perhaps a new cemetery is now operated by this operator?".format(cemetery_code))
        apply_category(Categories.GRAVE, item)
        if plot_number := feature.get("PlotNumber"):
            item["extras"]["alt_ref"] = str(plot_number)
        yield item
