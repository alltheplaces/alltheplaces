from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.geo import point_locations


class GreenwaySpider(Spider):
    name = "greenway"
    item_attributes = {
        "operator": "GreenWay",
        "operator_wikidata": "Q116450281",
        "extras": {"amenity": "charging_station"},
    }

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", ["PL", "SK"]):
            yield Request(
                url=f"https://api.greenwaypolska.pl/api/location/map?max_power[from]=1&connector_type[ccs_plug]=1&connector_type[chademo_plug]=1&connector_type[type2_plug]=1&connector_type[type2_socket]=1&latitude={lat}&longitude={lon}&spanLat=1&spanLng=1",
            )

    def parse(self, response):
        # TODO: get more place info from https://api.greenwaypolska.pl/api/location/{location_id}
        for node in response.json():
            item = {
                **dict(DictParser.parse(node)),
                "description": node["access_instructions"],
                "ref:EU:EVSE": node["code"],
                "charging_station:output": f'{node["max_power"]} kW',
                "capacity": node["total"],
            }
            yield item
