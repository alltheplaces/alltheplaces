from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EniSpider(Spider):
    name = "eni"
    item_attributes = {"brand": "Eni", "brand_wikidata": "Q565594"}
    countries = ["IT", "AT", "DE", "ES", "CH", "FR"]

    async def start(self) -> AsyncIterator[Any]:
        for country in self.countries:
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
            apply_category(Categories.FUEL_STATION, item)
            yield item
