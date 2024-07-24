from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class AllegroOneBoxPLSpider(Spider):
    name = "allegro_one_box_pl"
    item_attributes = {"brand": "Allegro One Box", "brand_wikidata": "Q110738715"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            method="GET",
            url="https://edge.allegro.pl/general-deliveries?nwLat=56.04770689192265&nwLon=2.5567803015399404&seLat=48.224919937057095&seLon=38.32826467653994&brandKeys=ALLEGRO_APM&deliveryMethods=0b257488-c85d-4507-b967-9b45ffbfa2e8&deliveryMethods=0aafb43c-e66a-46ec-9cc4-29bb39ebb483&sellerId=95826291&clusterThreshold=900000000",
            headers={"Accept": "application/vnd.allegro.public.v3+json"},
        )

    def parse(self, response: Response, **kwargs):
        data = response.json()

        for box in data["points"]:
            yield JsonRequest(
                url=f"https://edge.allegro.pl/general-deliveries/{box['id']}",
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
