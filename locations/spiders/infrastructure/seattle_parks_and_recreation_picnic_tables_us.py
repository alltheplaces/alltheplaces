from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationPicnicTablesUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_picnic_tables_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Picnic_Tables"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if ref := feature.get("AMWOID"):
            item["ref"] = ref
        else:
            item["ref"] = feature["OBJECTID"]
        item.pop("name", None)
        apply_category(Categories.LEISURE_PICNIC_TABLE, item)
        match feature.get("TABLE_MATERIAL"):
            case "Composite":
                item["extras"]["material"] = "composite"
            case "Metal":
                item["extras"]["material"] = "metal"
            case "Wood":
                item["extras"]["material"] = "wood"
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["TABLE_MATERIAL"]))
        if seat_count := feature.get("SEATING_CAP"):
            item["extras"]["seats"] = str(seat_count)
        yield item
