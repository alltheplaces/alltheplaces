from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MerGBSpider(Spider):
    name = "mer_gb"
    item_attributes = {"brand": "Mer", "brand_wikidata": "Q100821564"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://driver.uk.mer.eco/stationFacade/findSitesInBounds",
            data={
                "filterByBounds": {"northEastLat": 90, "northEastLng": 180, "southWestLat": -90, "southWestLng": -180}
            },
        )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            if location["deleted"]:
                continue

            item = DictParser.parse(location)
            item["street_address"] = location["dn"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
