from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AmtrakSpider(Spider):
    name = "amtrak"
    start_urls = ["https://maps.amtrak.com/services/MapDataService/stations/allStations"]

    station_types = {
        "BUS": Categories.BUS_STOP,
        "TRAIN": Categories.TRAIN_STATION,
    }
    shelter_types = {
        "Curbside Bus Stop only (no shelter)": {"shelter": "no"},
        "Platform only (no shelter)": {"shelter": "no"},
        "Platform with Shelter": {"shelter": "yes"},
        "Station Building (with waiting room)": {"shelter": "yes"},
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["StationsDataResponse"]["features"]:
            item = DictParser.parse(location["properties"])
            item["street_address"] = merge_address_lines(
                [location["properties"]["Address1"], location["properties"]["Address2"]]
            )
            item["ref"] = location["properties"]["Code"]
            if not item.get("name") or item["name"] == " ":
                item["name"] = location["properties"]["StationName"]
            item["website"] = "https://www.amtrak.com/stations/{}".format(location["properties"]["Code"].lower())

            if cat := self.station_types.get(location["properties"]["StnType"]):
                apply_category(cat, item)
            if details := self.shelter_types.get(location["properties"]["StaType"]):
                item["extras"].update(details)

            if aliases := location["properties"]["StationAliases"].strip():
                item["extras"]["alt_name"] = ";".join(aliases.split(","))

            yield item
