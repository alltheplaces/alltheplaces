from html import unescape
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HKFSDCareAEDsSpider(ArcGISFeatureServerSpider):
    name = "hkfsd_care_aeds"
    host = "portal.csdi.gov.hk"
    context_path = "server"
    service_id = "common/hkfsd_rcd_1695974242578_37917"
    layer_id = "0"

    item_attributes = {}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["located_in"] = unescape(feature["AED_Name"])
        item["addr_full"] = feature["AED_Addres"]
        item["extras"]["defibrillator:location"] = unescape(feature["Detailed_l"])
        item["extras"]["description"] = feature["AED_remark"]
        item["extras"]["manufacturer"] = feature["AED_brand"]
        item["extras"]["model"] = feature["AED_model"]

        apply_category(Categories.DEFIBRILLATOR, item)
        yield item
