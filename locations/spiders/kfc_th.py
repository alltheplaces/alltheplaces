from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcTHSpider(Spider):
    name = "kfc_th"
    item_attributes = KFC_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://orderserv-kfc-apac-olo-api.yum.com/dev/v1/stores",
            headers={"x-tenant-id": "59dhhptudcn7hk1ogssvsb4cujvbcnh6o"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not location["isActive"]:
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["location"]["latitude"]
            item["lon"] = location["location"]["longitude"]
            item["branch"] = location["name"].removeprefix("KFC ")
            item["operator"] = location["owner"]

            for address in location["localAddress"]:
                if address["lang"] == "lang":
                    item["street_address"] = merge_address_lines(address["address"]["addressLines"])
                    item["city"] = address["address"]["city"]
                    item["state"] = address["address"]["state"]
                    item["postcode"] = address["address"]["pinCode"]
                    item["country"] = address["address"]["country"]

            for contact in location["contacts"]:
                if contact["key"] == "phoneNumber":
                    item["phone"] = contact["value"]
                elif contact["key"] == "email":
                    item["email"] = contact["value"]

            yield item
