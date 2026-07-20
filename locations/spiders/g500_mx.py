from typing import Any, AsyncIterator

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class G500MXSpider(scrapy.Spider):
    name = "g500_mx"
    item_attributes = {"brand": "G500", "brand_wikidata": "Q115215326"}
    api_url = "https://g500network.com/wp-admin/admin-ajax.php"
    fuels = {"G Diesel": Fuel.DIESEL, "G Premium": Fuel.OCTANE_91, "G Super": Fuel.OCTANE_87}

    async def start(self) -> AsyncIterator[Any]:
        yield scrapy.FormRequest(
            url=self.api_url, formdata={"action": "get_allstations"}, callback=self.parse_all_stations
        )

    def parse_all_stations(self, response):
        for station in response.json():
            yield scrapy.FormRequest(
                url=self.api_url,
                formdata={"action": "get_station_byid", "id": station["id"]},
                callback=self.parse_station,
                cb_kwargs={"station_id": station["id"]},
            )

    def parse_station(self, response, station_id):
        store = response.json()[0]
        store["id"] = station_id
        store["state"] = store.pop("est")
        store["street-address"] = store.pop("add")
        store["town"] = store.pop("col")
        item = DictParser.parse(store)
        for fuel_id in store["gas_id"]:
            if fuel := self.fuels.get(fuel_id):
                apply_yes_no(fuel, item, True)
            else:
                self.crawler.stats.inc_value("atp/g500_mx/unmatched_fuel/{}".format(fuel_id))
        apply_category(Categories.FUEL_STATION, item)
        yield item
