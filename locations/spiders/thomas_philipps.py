from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ThomasPhilippsSpider(Spider):
    name = "thomas_philipps"
    item_attributes = {"brand": "Thomas Philipps", "brand_wikidata": "Q1424735"}

    def start_requests(self):
        yield JsonRequest(
            "https://www.thomas-philipps.de/od/maps/getLocations",
            data={
                "coordinateX": 52.52000659999999,
                "coordinateY": 13.404954,
                "listId": "5f1b4bf48edf4a7abc7856616fe5097c",
                "displayMode": "list",
                "count": 10000,
            },
        )

    def parse(self, response: Response):
        for store in response.json():
            opening_hours = OpeningHours()
            for day in store["openingHours"]:
                opening_hours.add_range(DAYS[day["weekDay"] - 1], day["opensAt"][-18:-13], day["closesAt"][-18:-13])
            feature = DictParser.parse(store)
            feature["ref"] = store["externalId"]
            feature["lat"], feature["lon"] = store["coordinatesX"], store["coordinatesY"]
            feature["street_address"] = feature.pop("street")
            feature["opening_hours"] = opening_hours
            if store["cover"]:
                feature["image"] = store["cover"]["url"]
            yield feature
