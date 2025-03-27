import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HobsonsBayCityCouncilPlaygroundsAUSpider(ArcGISFeatureServerSpider):
    name = "hobsons_bay_city_council_playgrounds_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    host = "services3.arcgis.com"
    context_path = "gToGKwidNkZbWBGJ/ArcGIS"
    service_id = "Playgrounds_Pt"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["central_as"]
        item["name"] = feature["site_name"]
        item["addr_full"] = re.sub(r"\s+", " ", feature["feature_lo"])
        apply_category(Categories.LEISURE_PLAYGROUND, item)
        yield item
