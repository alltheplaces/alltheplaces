from typing import Any, AsyncIterator

import scrapy
from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

FUEL_TYPES_MAPPING = {
    "adblue": Fuel.ADBLUE,
    "adblue erogatore": Fuel.ADBLUE,
    "benzina": Fuel.OCTANE_95,
    "gasolio": Fuel.DIESEL,
    "gpl": Fuel.LPG,
    "metano": Fuel.CNG,
    "optimo benzina": Fuel.OCTANE_95,
    "optimo diesel": Fuel.DIESEL,
    "optimo gasolio": Fuel.DIESEL,
}

PAYMENT_TYPES_MAPPING = {
    "ip plus": "payment:ip_plus",
    "postepay": PaymentMethods.POSTEPAY,
    "telepass": "payment:telepass",
}


class IpItSmSpider(Spider):
    name = "ip_it_sm"
    item_attributes = {"brand": "IP", "brand_wikidata": "Q3788748"}
    base_url = "https://ip.gruppoapi.com/ricerca-stazioni-servizio/station/"

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://ip.gruppoapi.com/ricerca-stazioni-servizio/api/search",
            formdata={
                "cornerNELat": "90",
                "cornerNELng": "180",
                "cornerSWLat": "-90",
                "cornerSWLng": "-180",
            },
            callback=self.parse_store_id,
        )

    def parse_store_id(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            url = self.base_url + store["stationCode"]
            yield scrapy.Request(url, callback=self.parse, cb_kwargs=dict(value=store))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store_details = kwargs["value"]
        item = DictParser.parse(store_details)
        item["city"] = store_details.get("place")
        if store_details["district"] == "SM":
            item["country"] = "SM"
        else:
            item["state"] = store_details["district"]
            item["country"] = "IT"
        item["website"] = response.url
        item["ref"] = store_details["stationCode"]
        self.parse_station_details(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item

    def parse_station_details(self, item: Feature, response: Response) -> None:
        for detail in response.xpath(
            '//div[@class="station-table"]//div[@class="single-detail"]/div[@class="text"]/text()'
        ).getall():
            detail = detail.strip().lower()
            if tag := FUEL_TYPES_MAPPING.get(detail):
                apply_yes_no(tag, item, True)
            elif tag := PAYMENT_TYPES_MAPPING.get(detail):
                apply_yes_no(tag, item, True)
            elif detail == "self 24 ore":
                item["opening_hours"] = "24/7"
