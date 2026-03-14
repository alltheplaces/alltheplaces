from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VicFreeWifiAUSpider(JSONBlobSpider):
    name = "vic_free_wifi_au"
    item_attributes = {"operator": "Victorian State Government", "operator_wikidata": "Q5589335"}
    allowed_domains = ["www.vic.gov.au"]
    start_urls = ["https://www.vic.gov.au/api/tide/elasticsearch/sdp_data_pipelines_vicfreewifi/_search?size=10000"]
    locations_key = ["hits", "hits"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("_source"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["name"]
        item["name"] = feature["site"]
        apply_category(Categories.ANTENNA, item)
        item["extras"]["internet_access"] = "wlan"
        item["extras"]["internet_access:fee"] = "no"
        item["extras"]["internet_access:operator"] = "TPG Telecom"
        item["extras"]["internet_access:operator:wikidata"] = "Q7939276"
        item["extras"]["internet_access:ssid"] = "VicFreeWiFi"
        yield item
