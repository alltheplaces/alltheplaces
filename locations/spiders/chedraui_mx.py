from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ChedrauiMXSpider(Spider):
    name = "chedraui_mx"
    item_attributes = {"brand": "Chedraui", "brand_wikidata": "Q2961952"}
    allowed_domains = ["www.chedraui.com.mx"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.chedraui.com.mx/_v/public/graphql/v1",
            data={"query": """
                query @context(sender:"chedrauimx.locator@2.x",provider:"vtex.store-graphql@2.x"){
                  documents(pageSize:1000,acronym:"CS",fields:["id_store","full_name","address","postal_code","city","state","latitude","longitude","open_hour","close_hour","home_delivery","parking_bikes","parking_cars","parking_motos","parking_for_disabled","parking_pickup","store_pickup"]) {
                      fields {
                            key
                            value
                        }
                    }
                }"""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json()["data"]["documents"]:
            store = {field["key"]: field["value"] for field in data["fields"] if not field["value"] == "null"}
            if not isinstance(store.get("full_name"), str):
                continue
            store["latitude"], store["longitude"] = [
                coord.replace(",", ".", 1).replace(",", "")
                for coord in [store.get("latitude", ""), store.get("longitude", "")]
            ]
            item = DictParser.parse(store)
            item["branch"] = store.get("full_name").replace("Chedraui ", "")
            item["street_address"] = item.pop("addr_full")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(f"Mo-Su {store.get('open_hour')} - {store.get('close_hour')}")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            apply_yes_no(Extras.DELIVERY, item, store.get("home_delivery") == "Si")
            apply_yes_no(Extras.PARKING_WHEELCHAIR, item, store.get("parking_for_disabled") == "Si")
            apply_yes_no("drive_in", item, store.get("parking_pickup") == "Si")
            yield item
