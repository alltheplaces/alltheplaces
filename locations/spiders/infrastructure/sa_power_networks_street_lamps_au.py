from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SaPowerNetworksStreetLampsAUSpider(JSONBlobSpider):
    name = "sa_power_networks_street_lamps_au"
    item_attributes = {"operator": "SA Power Networks", "operator_wikidata": "Q7388891", "state": "SA"}
    allowed_domains = ["slo.apps.sapowernetworks.com.au"]
    start_urls = [
        "https://slo.apps.sapowernetworks.com.au/WebServices/StreetLightService.svc/GetStreetLightsGeoLocation?northEastLatitude=-25.9&northEastLongitude=135&southWestLatitude=-32&southWestLongitude=128.9",
        "https://slo.apps.sapowernetworks.com.au/WebServices/StreetLightService.svc/GetStreetLightsGeoLocation?northEastLatitude=-25.9&northEastLongitude=141&southWestLatitude=-32&southWestLongitude=135",
        "https://slo.apps.sapowernetworks.com.au/WebServices/StreetLightService.svc/GetStreetLightsGeoLocation?northEastLatitude=-32&northEastLongitude=135&southWestLatitude=-38.1&southWestLongitude=128.9",
        "https://slo.apps.sapowernetworks.com.au/WebServices/StreetLightService.svc/GetStreetLightsGeoLocation?northEastLatitude=-32&northEastLongitude=141&southWestLatitude=-38.1&southWestLongitude=135",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.STREET_LAMP, item)
        yield item
