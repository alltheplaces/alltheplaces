from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilManholesUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_manholes_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "Manhole"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FacilityID"]
        apply_category(Categories.MANHOLE, item)
        if alt_ref := feature.get("AsBuiltNumber"):
            item["extras"]["alt_ref"] = alt_ref
        if diameter_in := feature.get("Diameter"):
            if int(diameter_in) > 0:
                item["extras"]["diameter"] = f"{diameter_in}\""
        yield item
