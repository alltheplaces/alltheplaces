from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.spiders.taco_bell import TACO_BELL_SHARED_ATTRIBUTES


class TacoBellESSpider(Spider):
    name = "taco_bell_es"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="https://loyalty-customer-api.pro.tacobell.es/public/store/list?paginationMaxItems=100&paginationOffset={}&showOrder=distance&model.idStoreStatusStore=1".format(
                offset
            ),
            headers={
                "X-Auth-Token": "s1ktt2qz7tiis5sut4yer4gv7mx4qm6h3u4erplzs7avaopwv5wotdpzj9f6cg85gqydxk07md86f2n1ykvgxjizcpnx6hloa3pxkphdilsab5fwnn0o950y5xx4igio"
            },
            meta={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["list"]:
            item = Feature()
            item["ref"] = location["idStore"]
            item["branch"] = location["descriptionStore"].removeprefix("Taco Bell").strip()
            item["street_address"] = location["addressStore"]
            item["city"] = location["cityStore"]
            item["state"] = location["nameProvince"]
            item["postcode"] = location["postCodeStore"]
            item["lat"] = location["latitudeStore"]
            item["lon"] = location["longitudeStore"]

            apply_yes_no(Extras.DRIVE_THROUGH, item, location["drivethruStore"])

            item["website"] = item["extras"]["website:es"] = "https://tacobell.es/es/restaurantes/{}/{}".format(
                location["idProvinceStore"], location["idStore"]
            )
            item["extras"]["website:ca"] = "https://tacobell.es/ca/restaurants/{}/{}".format(
                location["idProvinceStore"], location["idStore"]
            )
            item["extras"]["website:en"] = "https://tacobell.es/en/restaurants/{}/{}".format(
                location["idProvinceStore"], location["idStore"]
            )

            yield item

        if len(response.json()["data"]["list"]) == 100:
            yield self.make_request(response.meta["offset"] + 100)
