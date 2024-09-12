from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class GreenwayPLSKSpider(Spider):
    name = "greenway_pl_sk"
    item_attributes = {
        "operator": "GreenWay",
        "operator_wikidata": "Q116450281",
        "extras": Categories.CHARGING_STATION.value,
    }

    def start_requests(self) -> Iterable[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["PL", "SK"], 48):
            yield JsonRequest(
                url=f"https://api.greenwaypolska.pl/api/location/map?max_power[from]=1&connector_type[ccs_plug]=1&connector_type[chademo_plug]=1&connector_type[type2_plug]=1&connector_type[type2_socket]=1&latitude={lat}&longitude={lon}&spanLat=1&spanLng=1",
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json()

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        # TODO: get more place info from https://api.greenwaypolska.pl/api/location/{location_id}
        for feature in features:
            item = DictParser.parse(feature)
            item["extras"]["description"] = feature["access_instructions"]
            item["extras"]["ref:EU:EVSE"] = feature["code"]
            item["extras"]["charging_station:output"] = str(feature["max_power"]) + " kW"
            item["extras"]["capacity"] = feature["total"]
            yield item
