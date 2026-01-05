from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilSewerManholesCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_sewer_manholes_ca"
    item_attributes = {"operator": "Niagara Falls City Council", "operator_wikidata": "Q16941501", "state": "ON"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Sanitary_Sewer_Maintenance_Holes"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Status") != "ACTIVE":
            return
        if ref := feature.get("ID"):
            item["ref"] = ref
        else:
            item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.MANHOLE, item)
        item["extras"]["manhole"] = "sewer"
        yield item
