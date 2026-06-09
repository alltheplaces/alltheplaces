from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MoilTRSpider(Spider):
    name = "moil_tr"
    item_attributes = {"brand": "Moil", "brand_wikidata": "Q62296914"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://oyakakaryakit.lokasyonanalizi.com/api/locator/total/getPois2/",
            data={"searchText": "", "brand": "moil", "city": None, "county": None, "options": []},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location["city"] = location["cityName"]
            location["state"] = location["countyName"]
            item = DictParser.parse(location)
            item["name"] = item["name"].strip()
            item["addr_full"] = location["info"]["address"]
            apply_category(Categories.FUEL_STATION, item)
            print(item["lat"], item["lon"])
            yield item
