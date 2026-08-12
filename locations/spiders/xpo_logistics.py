from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class XpoLogisticsSpider(ArcGISFeatureServerSpider):
    name = "xpo_logistics"
    item_attributes = {"brand": "XPO Logistics", "brand_wikidata": "Q8042415"}
    host = "maps.xpo.com"
    context_path = "ltlbisvc"
    service_id = "ServiceMap/PRODUCTION_Service_Map_SIC"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("sic_cd")
        item["name"] = feature.get("terminal_nm")
        item["phone"] = feature.get("terminal_phone")
        apply_category(Categories.OFFICE_COURIER, item)
        yield item
