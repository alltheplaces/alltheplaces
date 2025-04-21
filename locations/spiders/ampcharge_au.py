from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

CONNECTORS = {
    "CHAdeMO": "chademo",
    "CCS2": "type2_combo",
}


class AmpchargeAUSpider(Spider):
    name = "ampcharge_au"
    item_attributes = {"name": "AmpCharge", "operator": "AmpCharge", "operator_wikidata": "Q111744561"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://digital-api.ampol.com.au/siteservice/Service/Ext.Closest(lg=115.76657537179369,lt=-32.340979786001604,distance=4000000)?$filter=(EVFastCharging+eq+true)",
            headers={"ocp-apim-subscription-key": "fd5342b7b7304260910be1d73a296114"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["value"]:
            item = Feature()
            item["branch"] = location["LocationName"]
            item["lon"], item["lat"] = location["Location"]["coordinates"]
            item["ref"] = location["LocationID"]
            item["street_address"] = location["Address"]
            for connector in location["AmpChargeData"]["Connectors"]:
                if tag := CONNECTORS.get(connector["ConnectorType"]):
                    item["extras"]["socket:{}".format(tag)] = str(connector["TotalConnectors"])
                else:
                    self.logger.error("Unexpected connector type: {}".format(connector["ConnectorType"]))

            apply_category(Categories.CHARGING_STATION, item)

            yield item
