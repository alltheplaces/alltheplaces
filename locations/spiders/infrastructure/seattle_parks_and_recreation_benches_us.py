from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationBenchesUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_benches_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Park_Bench"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if ref := feature.get("AMWOID"):
            item["ref"] = ref
        else:
            item["ref"] = feature["OBJECTID"]
        apply_category(Categories.BENCH, item)
        match feature.get("BNCH_MAT"):
            case "Composite/Metal":
                item["extras"]["material"] = "composite;metal"
            case "Concrete":
                item["extras"]["material"] = "concrete"
            case "Metal":
                item["extras"]["material"] = "metal"
            case "Wood/Concrete":
                item["extras"]["material"] = "concrete;wood"
            case "Wood/Metal":
                item["extras"]["material"] = "metal;wood"
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["BNCH_MAT"]))
        if length := feature.get("BNCH_LGTH"):
            item["extras"]["length"] = f"{length}'"
        yield item
