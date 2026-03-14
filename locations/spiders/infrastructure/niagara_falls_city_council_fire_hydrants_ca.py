from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilFireHydrantsCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_fire_hydrants_ca"
    item_attributes = {"operator": "Niagara Falls City Council", "operator_wikidata": "Q16941501", "state": "ON"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Hydrants"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["HydrantID"]
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.FIRE_HYDRANT, item)
        yield item
