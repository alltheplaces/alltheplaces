from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HastingsDistrictCouncilPlaygroundsNZSpider(ArcGISFeatureServerSpider):
    name = "hastings_district_council_playgrounds_nz"
    item_attributes = {"operator": "Hastings District Council", "operator_wikidata": "Q73811101"}
    host = "gismaps.hdc.govt.nz"
    context_path = "server"
    service_id = "ParksReserves/Parks_and_Reserves"
    server_type = "MapServer"
    layer_id = "1"
    requires_proxy = True  # Data centre IP ranges appear to be blocked.

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["name"]  = feature["TAG"]
        apply_category(Categories.LEISURE_PLAYGROUND, item)
        yield item
