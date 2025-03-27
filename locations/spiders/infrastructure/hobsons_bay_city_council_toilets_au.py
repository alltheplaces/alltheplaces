from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HobsonsBayCityCouncilToiletsAUSpider(ArcGISFeatureServerSpider):
    name = "hobsons_bay_city_council_toilets_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    host = "services3.arcgis.com"
    context_path = "gToGKwidNkZbWBGJ/ArcGIS"
    service_id = "Public_Toilets_Pt"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["central_as"]
        item["name"] = feature["site_name"]
        apply_category(Categories.TOILETS, item)
        item["extras"]["access"] = "yes"
        item["extras"]["fee"] = "no"
        yield item
