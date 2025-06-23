from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

SOCKET_TYPES = {
    "CCS1": "type1_combo",
    "CCS2": "type2_combo",
    "CHAdeMO": "chademo",
    "GBT": "gb_ac",
    "J1772": "type1",
    "MENNEKES": "type2",
    "NACS": "nacs",
}


class BlinkSpider(Spider):
    name = "blink"
    item_attributes = {
        "brand": "Blink",
        "brand_wikidata": "Q62065645",
        "operator": "Blink",
        "operator_wikidata": "Q62065645",
    }

    # First request the map, but it only returns lat/lon/ID for each station
    def start_requests(self):
        yield JsonRequest(
            "https://apigw.blinknetwork.com/nmap/v3/locations/map/pins",
            data={
                "latitude": 0,
                "longitude": 0,
                "radius": 25000,
            },
            callback=self.parse_pins,
        )

    # For each station, request details, and pass through lat/lon
    def parse_pins(self, response):
        for pin in response.json():
            yield JsonRequest(
                f"https://apigw.blinknetwork.com/v3/locations/map/{pin['locationId']}",
                callback=self.parse_station,
                cb_kwargs={"lat": pin["latitude"], "lon": pin["longitude"]},
            )

    def parse_station(self, response, lat, lon):
        location = response.json()
        item = DictParser.parse(location)

        item["lat"] = lat
        item["lon"] = lon
        item["branch"] = item.pop("name")
        apply_category(Categories.CHARGING_STATION, item)

        oh = OpeningHours()
        for line in location["locationSchedule"]["locationScheduleInfoDTO"]:
            if line["isOpen"]:
                oh.add_range(line["weekDay"], line["startTime"], line["endTime"])
            else:
                oh.set_closed(line["weekDay"])
        item["opening_hours"] = oh

        yield item

        # Additionally request details about the chargers
        yield JsonRequest(
            f"https://apigw.blinknetwork.com/v3/locations/{location['locationId']}",
            callback=self.parse_points,
            cb_kwargs={"parent": item},
        )

    def parse_points(self, response, parent):
        for level in response.json():
            for charger in level["chargers"]:
                item = Feature(
                    city=parent.get("city"),
                    country=parent.get("country"),
                    geometry=parent.get("geometry"),
                    opening_hours=parent.get("opening_hours"),
                    postcode=parent.get("postcode"),
                    state=parent.get("state"),
                    street_address=parent.get("street_address"),
                )
                apply_category({"man_made": "charge_point"}, item)
                item["name"] = charger["portName"]
                # For OSM tagging, "ref" is probably better, but ref needs to be globally unique in ATP
                item["extras"]["ref:serial"] = charger["serialNumber"]
                item["ref"] = charger["portId"]

                socket_type = SOCKET_TYPES.get(charger["connectorType"])
                if socket_type is None:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_socket/{charger['connectorType']}")
                else:
                    apply_yes_no(f"socket:{socket_type}", item, True)
                    item["extras"][f"socket:{socket_type}:output"] = str(round(charger["maxPower"] / 1000, 1))
                    item["extras"][f"socket:{socket_type}:voltage"] = str(charger["maxVoltage"])
                    item["extras"][f"socket:{socket_type}:current"] = str(charger["maxCurrent"])

                if charger["isRestricted"]:
                    item["extras"]["access"] = "private"

                yield item
