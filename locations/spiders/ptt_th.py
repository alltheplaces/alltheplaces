from copy import deepcopy
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class PttTHSpider(Spider):
    name = "ptt_th"
    item_attributes = {"brand_wikidata": "Q1810389"}
    JIFFY = {"brand": "Jiffy", "brand_wikidata": "Q16770436"}
    TEXAS_CHICKEN = {"brand": "Texas Chicken", "brand_wikidata": "Q1089932"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.pttstation.com/mobilecontrol/list_station",
            data={
                "page": str(page),
                "limit": "100",
                "station_type": "",
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
            location_type = location["type"].upper()
            if location_type not in ["OIL", "TEXAS CHICKEN"]:
                continue
            item = Feature()
            item["branch"] = location["name"]
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["addr_full"] = location["address"]
            item["city"] = location["province_name"]
            item["website"] = item["extras"]["website:th"] = location["link_share"]
            item["extras"]["website:en"] = location["link_share"].replace("/th?", "/en?")

            services = [service["id"] for service in location["service"]]

            if location_type == "TEXAS CHICKEN":
                item.update(self.TEXAS_CHICKEN)
                apply_category({"amenity": "fast_food", "cuisine": "chicken"}, item)
            else:
                if "2" in services:  # Jiffy shops co-located with PTT stations
                    shop = deepcopy(item)
                    shop.update(self.JIFFY)
                    shop["ref"] += "_jiffy"
                    shop["located_in"] = "ป.ต.ท."
                    shop["located_in_wikidata"] = self.item_attributes["brand_wikidata"]
                    apply_category(Categories.SHOP_CONVENIENCE, shop)
                    yield shop

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
