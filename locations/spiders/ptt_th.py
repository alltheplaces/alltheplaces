from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class PttTHSpider(Spider):
    name = "ptt_th"
    item_attributes = {"brand_wikidata": "Q1810389"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.pttstation.com/mobilecontrol/list_station",
            data={
                "page": str(page),
                "limit": "100",
                "station_type": "OIL",
                "product_id": "",
                "service_id": "",
                "keyword": "",
                "province": "",
                "amphur": "",
                "ngv_type": "",
                "clat": "0",
                "clng": "0",
                "station_id": "",
                "near_type": "",
                "bound_type": "",
                "promotion_id": "",
                "country_type_id": "1",
                "language": "th",
            },
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = Feature()
            item["branch"] = location["name"]
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["addr_full"] = location["address"]
            item["city"] = location["province_name"]
            item["website"] = item["extras"]["website:th"] = location["link_share"]
            item["extras"]["website:en"] = location["link_share"].replace("/th?", "/en?")

            apply_category(Categories.FUEL_STATION, item)

            products = [product["name"] for product in location["product"]]

            # TODO: "GSH 95 Premium", "Hi-speed Diesel B7","Premium Hi-speed Diesel B7"
            apply_yes_no(Fuel.ELECTRIC, item, "EV" in products)
            apply_yes_no(Fuel.OCTANE_91, item, "GASOHOL 91" in products)
            apply_yes_no(Fuel.E20, item, "GASOHOL 95-E20" in products)
            apply_yes_no(Fuel.E85, item, "GASOHOL 95-E85" in products)
            apply_yes_no(Fuel.DIESEL, item, "Hi-speed Diesel" in products)
            apply_yes_no(Fuel.OCTANE_95, item, "Unlead Gas 95" in products)

            yield item

        if response.json()["data"]:
            yield self.make_request(response.meta["page"] + 1)
