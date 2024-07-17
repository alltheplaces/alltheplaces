from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KFCCASpider(Spider):
    name = "kfc_ca"
    item_attributes = KFC_SHARED_ATTRIBUTES | {"name": "KFC", "nsi_id": "N/A"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://orderserv-kfc-na-olo-api.yum.com/dev/v1/stores",
            headers={"x-tenant-id": "a087813cef074625a8341e162356a1e5"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not location["isActive"]:
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["location"]["latitude"]
            item["lon"] = location["location"]["longitude"]
            item["operator"] = location["owner"]
            address = location["localAddress"][0]["address"]
            item["street_address"] = merge_address_lines(address["addressLines"])
            item["city"] = address["city"]
            item["state"] = address["state"]
            item["postcode"] = address["pinCode"]

            for contact in location["contacts"]:
                if contact["key"] == "email":
                    item["email"] = contact["value"]
                elif contact["key"] == "phoneNumber":
                    item["phone"] = contact["value"]

            apply_category(Categories.FAST_FOOD, item)

            yield item
