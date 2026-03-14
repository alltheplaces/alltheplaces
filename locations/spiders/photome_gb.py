from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class PhotomeGBSpider(ArcGISFeatureServerSpider):
    name = "photome_gb"
    item_attributes = {"brand": "Photo-Me", "brand_wikidata": "Q123456627"}
    host = "services5.arcgis.com"
    context_path = "M6ZM30o7d7nGnSp2/arcgis"
    service_id = "Photo_Me_map_220223"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Lookup"]
        item["branch"] = feature["place_name"]
        apply_category(Categories.PHOTO_BOOTH, item)
        yield item
