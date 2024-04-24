from typing import Iterable

from scrapy import FormRequest, Request, Spider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature

FUEL_MAPING = {
    "100plus": Fuel.OCTANE_100,
    "92": Fuel.OCTANE_92,
    "95": Fuel.OCTANE_95,
    "95plus": Fuel.OCTANE_95,
    "DT": Fuel.DIESEL,
    "DTplus": Fuel.DIESEL,
}


class TeboilRUSpider(Spider):
    name = "teboil_ru"
    item_attributes = {"brand": "Teboil", "brand_wikidata": "Q7692079"}
    allowed_domains = ["azs.teboil.ru"]

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            url="https://azs.teboil.ru/map/ajax/map.php",
            formdata={"cityId[]": ""},
        )

    def parse(self, response):
        for poi in response.json()["data"][0]["shops"]:
            item = Feature()
            # data is a bit messy, 'telephone' in most cases has has POI id
            item["ref"] = poi.get("externalCode") if poi.get("externalCode") != "" else poi.get("telephone")
            item["addr_full"] = poi["adr"]
            item["lat"], item["lon"] = poi["coordinates"]
            apply_category(Categories.FUEL_STATION, item)
            self.parse_fuel(item, poi)
            yield item

    def parse_fuel(self, item, poi):
        if fuels := poi.get("fuel"):
            for fuel in fuels:
                if tag := FUEL_MAPING.get(fuel["fuelId"]):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f'atp/teboil_ru/fuel/unknown/{fuel["fuelId"]}')
