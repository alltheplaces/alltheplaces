from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class NewEngland511USSpider(Spider):
    """
    A number of US states share a common Travel-IQ traffic information system
    and website. Usually TravelIQSpider storefinder could be used, but in this
    case the API has been disabled so an alternative spider is required.
    """
    name = "new_england_511_us"
    allowed_domains = ["www.newengland511.org"]
    start_urls = ['https://www.newengland511.org/List/GetData/Cameras?query={"columns":[{"data":null,"name":""},{"name":"sortId","s":true},{"name":"state","s":true},{"name":"roadway","s":true},{"name":"description1"},{"data":5,"name":""}],"order":[{"column":2,"dir":"asc"},{"column":1,"dir":"asc"}],"start":0,"length":100,"search":{"value":""}}&lang=en-US']
    operators = {
        "ME": ["Maine Department of Transportation", "Q4926312"],
        "NH": ["New Hampshire Department of Transportation", "Q5559073"],
        "VT": ["Vermont Agency of Transportation", "Q7921675"],
    }

    def parse(self, response: Response) -> Iterable[JsonRequest | Feature]:
        for start in range(100, response.json()["recordsFiltered"], 100):
            yield JsonRequest(url=response.url.replace('%22start%22:0', '%22start%22:{}'.format(start)), callback=self.parse_cameras)
        yield from self.parse_cameras(response)

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        for camera in response.json()["data"]:
            properties = {
                "ref": camera["id"],
                "name": camera["displayName"],
                "lat": camera["latitude"],
                "lon": camera["longitude"],
                "state": camera["organizationCenterId"],
                "operator": self.operators[camera["organizationCenterId"]][0],
                "operator_wikidata": self.operators[camera["organizationCenterId"]][1],
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            properties["extras"]["contact:webcam"] = "https://www.newengland511.org/tooltip/Cameras/{}".format(properties["ref"])
            properties["extras"]["camera:type"] = "fixed"
            yield Feature(**properties)
