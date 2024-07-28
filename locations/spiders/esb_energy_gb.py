import logging

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EsbEnergyGBSpider(Spider):
    name = "esb_energy_gb"
    item_attributes = {"brand": "ESB Energy", "brand_wikidata": "Q118261834"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://myevaccount.esbenergy.co.uk/stationFacade/findSitesInBounds",
            data={
                "filterByBounds": {"northEastLat": 90, "northEastLng": 180, "southWestLat": -90, "southWestLng": -180}
            },
        )

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            self.log(response.json()["errors"], logging.ERROR)
            return
        for location in response.json()["data"][1]:
            if location["deleted"]:
                continue

            item = DictParser.parse(location)
            item["street_address"] = location["dn"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
