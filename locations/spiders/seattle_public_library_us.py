from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattlePublicLibraryUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_public_library_us"
    item_attributes = {
        "name": "Seattle Public Library",
        "operator": "Seattle Public Library",
        "operator_wikidata": "Q7442157",
        "state": "WA",
    }
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Seattle_Public_Library"
    layer_id = "0"
    where_query = "NAME <> 'MOBILE SERVICES'"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OBJECTID"]
        item["branch"] = feature["LABEL"]
        item.pop("name", None)
        apply_category(Categories.LIBRARY, item)
        yield item
