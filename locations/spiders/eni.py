from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Access, Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class EniSpider(Spider):
    name = "eni"
    item_attributes = {"brand": "Eni", "brand_wikidata": "Q565594"}

    async def start(self) -> AsyncIterator[Any]:
        for country in ["IT", "AT", "DE", "ES", "CH", "FR"]:
            yield JsonRequest(
                url="https://stationfinder.enilive.it/webruntime/api/apex/execute?language=en&asGuest=true&htmlEncode=false",
                data={
                    "namespace": "",
                    "classname": "@udd/01pdY0000007KdB",
                    "method": "getPvs",
                    "isContinuation": False,
                    "params": {"countryCode": country},
                    "cacheable": False,
                },
                cb_kwargs={"country": country},
            )

    def parse(self, response: Response, country: str, **kwargs: Any) -> Any:
        for station in response.json().get("returnValue", {}).get("records", []):
            item = DictParser.parse(station)
            item["street_address"] = station.get("indirizzoPv")
            item["postcode"] = station.get("capPv")
            item["city"] = station.get("comunePv")
            if latitude := station.get("latitudine"):
                item["lat"] = latitude
            if longitude := station.get("longitudine"):
                item["lon"] = longitude
            item["country"] = country

            if station.get("temporaryClosed") is True:
                item["opening_hours"] = "closed"

            if station.get("eniCafe") is True:
                cafe = item.deepcopy()
                cafe["ref"] = "{}_cafe".format(item["ref"])
                apply_category(Categories.CAFE, cafe)
                yield cafe
            if station.get("eniWash") is True:
                car_wash = item.deepcopy()
                car_wash["ref"] = "{}_car_wash".format(item["ref"])
                apply_category(Categories.CAR_WASH, car_wash)
                yield car_wash

            apply_yes_no(Access.HGV, item, station.get("truck") is True)
            apply_yes_no(Extras.CAR_WASH, item, station.get("carWash") is True)
            apply_category(Categories.FUEL_STATION, item)

            yield item
