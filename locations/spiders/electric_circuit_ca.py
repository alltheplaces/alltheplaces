from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ElectricCircuitCASpider(Spider):
    name = "electric_circuit_ca"
    item_attributes = {"brand_wikidata": "Q24934590"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            "https://api.lecircuitelectrique.com/public/v1/configs",
            headers={
                "Authorization": "Basic SHl1alRsUWpTSkN0YzZNaEtIRDZJQzEzTDNXS3JJcm46QTlLdzhoZVlMMmZxVFRWRlRnZnVYdFF1YlVxOU14R1Y=",
                "Origin": "https://sites-map.lecircuitelectrique.com",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            "https://api.lecircuitelectrique.com/public/v1/sites/all?hidePartnerNetworkIds={}".format(
                ",".join(p["id"] for p in response.json()["site"]["partnerNetworks"])
            ),
            headers={
                "Authorization": "Basic SHl1alRsUWpTSkN0YzZNaEtIRDZJQzEzTDNXS3JJcm46QTlLdzhoZVlMMmZxVFRWRlRnZnVYdFF1YlVxOU14R1Y=",
                "Origin": "https://sites-map.lecircuitelectrique.com",
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location.get("isVisible") is not True:
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["address"]["location"]["lat"]
            item["lon"] = location["address"]["location"]["lng"]

            apply_category(Categories.CHARGING_STATION, item)

            yield item
