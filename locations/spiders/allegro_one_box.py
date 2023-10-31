from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class AllegroOneBoxSpider(Spider):
    name = "allegro_one_box_pl"
    item_attributes = {"brand": "Allegro One Box", "brand_wikidata": "Q110738715"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            method="GET",
            url="https://edge.allegro.pl/general-deliveries?nwLat=56.04770689192265&nwLon=2.5567803015399404&seLat=48.224919937057095&seLon=38.32826467653994&brandKeys=ALLEGRO_APM&clusterThreshold=900000000",
            headers={"Accept": "application/vnd.allegro.public.v3+json"},
        )

    def parse(self, response: Response, **kwargs):
        data = response.json()

        for box in data["points"]:
            properties = DictParser.parse(box)
            del properties["name"]
            properties["website"] = f"https://allegro.pl/kampania/one/znajdz-nas?pointId={box['id']}"
            yield properties
