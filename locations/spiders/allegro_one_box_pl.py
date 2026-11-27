from typing import AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser

POINT_LIMIT = 10000


class AllegroOneBoxPLSpider(Spider):
    name = "allegro_one_box_pl"
    item_attributes = {"brand": "Allegro One Box", "brand_wikidata": "Q110738715"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_box_request(self, nw_lat: float, nw_lon: float, se_lat: float, se_lon: float) -> Request:
        return Request(
            url=f"https://edge.allegro.pl/general-deliveries?nwLat={nw_lat}&nwLon={nw_lon}&seLat={se_lat}&seLon={se_lon}&brandKeys=ALLEGRO_APM&deliveryMethods=0b257488-c85d-4507-b967-9b45ffbfa2e8&deliveryMethods=0aafb43c-e66a-46ec-9cc4-29bb39ebb483&sellerId=95826291&clusterThreshold=900000000",
            headers={"Accept": "application/vnd.allegro.public.v3+json"},
            cb_kwargs={"box": (nw_lat, nw_lon, se_lat, se_lon)},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_box_request(56.04770689192265, 2.5567803015399404, 48.224919937057095, 38.32826467653994)

    def parse(self, response: Response, box: tuple[float, float, float, float]):
        points = response.json()["points"]

        if len(points) >= POINT_LIMIT:
            nw_lat, nw_lon, se_lat, se_lon = box
            mid_lat = (nw_lat + se_lat) / 2
            mid_lon = (nw_lon + se_lon) / 2
            yield self.make_box_request(nw_lat, nw_lon, mid_lat, mid_lon)
            yield self.make_box_request(nw_lat, mid_lon, mid_lat, se_lon)
            yield self.make_box_request(mid_lat, nw_lon, se_lat, mid_lon)
            yield self.make_box_request(mid_lat, mid_lon, se_lat, se_lon)
            return

        for box_point in points:
            yield JsonRequest(
                url=f"https://edge.allegro.pl/general-deliveries/{box_point['id']}",
                headers={"Accept": "application/vnd.allegro.public.v6+json"},
                callback=self.parse2,
            )

    def parse2(self, response):
        data = response.json()
        properties = DictParser.parse(data)
        del properties["name"]
        properties["website"] = f"https://allegro.pl/kampania/one/znajdz-nas?pointId={data['id']}"
        properties["ref"] = data["carrierPointId"]
        properties["extras"]["description"] = data["description"]
        properties["street_address"] = properties["street"]
        properties["street"] = None
        if data["openingTimesLabels"][0]["days"] == "całodobowo":
            properties["opening_hours"] = "24/7"
        yield properties
