import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class RepublicaUYSpider(ArcGISFeatureServerSpider):
    name = "republica_uy"
    item_attributes = {"brand": "República", "brand_wikidata": "Q4077337"}
    host = "services8.arcgis.com"
    context_path = "L7tmljogVEu5CMWs/arcgis"
    service_id = "Servicios_RedBROU"
    layer_id = "0"
    # The layer also lists third-party correspondent networks (REDPAGOS, ABITAB, SCANNTECH, URUPAGO); keep
    # only BROU's own branches (TIPO ends "SUC") and self-service ATM islands (TIPO ends "ISLA").
    where_query = "TIPO LIKE '%SUC' OR TIPO LIKE '%ISLA'"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)  # DIRECCION is the street line only
        item["city"] = feature.get("LOCALIDAD")
        item["state"] = feature.get("DEPARTAMENTO")
        # LOCAL is prefixed with an internal point number (e.g. "001-AIGUA", "179 - AG..."); keep the label.
        item["name"] = re.sub(r"^\d+\s*-\s*", "", feature.get("LOCAL") or "").strip() or None
        if "SUC" in feature["TIPO"]:
            item["branch"] = item.pop("name")  # branch label belongs in branch; NSI supplies the brand name
            apply_category(Categories.BANK, item)
        else:  # self-service ATM island keeps its location label as name
            apply_category(Categories.ATM, item)
        yield item
