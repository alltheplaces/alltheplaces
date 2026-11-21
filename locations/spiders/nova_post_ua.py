from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class NovaPostUASpider(Spider):
    name = "nova_post_ua"
    allowed_domains = ["api.novaposhta.ua"]
    page_size = 1000

    def request_page(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://api.novaposhta.ua/v2.0/json/",
            data={
                "apiKey": "",
                "modelName": "AddressGeneral",
                "calledMethod": "getWarehouses",
                "methodProperties": {"Page": str(page), "Limit": str(self.page_size)},
            },
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.request_page(1)

    def parse(self, response: Response, page: int) -> Any:
        locations = response.json()["data"]
        for location in locations:
            if location["WarehouseStatus"] != "Working" or location["CategoryOfWarehouse"] == "Fulfillment":
                continue
            item = Feature()
            item["ref"] = location["Ref"]
            item["branch"] = location["Number"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            item["street_address"] = location["Description"].split(": ", 1)[-1]
            item["city"] = location["SettlementDescription"]
            item["state"] = location["SettlementAreaDescription"]
            item["postcode"] = location["PostalCodeUA"]

            if location["CategoryOfWarehouse"] == "Postomat":
                item["brand"] = item["name"] = "Нова Пошта"
                item["brand_wikidata"] = "Q12133863"
                apply_category(Categories.PARCEL_LOCKER, item)
                if location["PostMachineType"] in ("ForResidentsOfEntrance", "LimitedAccess", "Private"):
                    item["extras"]["access"] = "private"
            else:
                item["operator"] = "Нова Пошта"
                item["operator_wikidata"] = "Q12133863"
                apply_category(Categories.POST_OFFICE, item)

            item["opening_hours"] = OpeningHours()
            for day, hours in location["Schedule"].items():
                if hours == "-":
                    item["opening_hours"].set_closed(DAYS_EN[day])
                else:
                    open_time, close_time = hours.split("-")
                    item["opening_hours"].add_range(DAYS_EN[day], open_time.replace("00:01", "00:00"), close_time)
            yield item

        if len(locations) == self.page_size:
            yield self.request_page(page + 1)
