from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TravelIQWebCamerasSpider(Spider):
    """
    Travel-IQ is a real-time road vehicle traffic management system used
    extensively in North America for providing the public with the following
    types of information:
    - Congestion
    - Variable speed limit changes
    - Roadworks
    - Traffic accidents
    - Weather information
    - Webcam feeds

    Usually TravelIQSpider could be used to retrieve information but in some
    rarer cases, a state transportation agency/department may be providing
    a Travel-IQ system with the official API disabled. This typically occurs
    when there is no corresponding mobile application and all users are
    required to use a web browser instead.

    This storefinder class implements an alternative type of API used by web
    browser sessions for retrieving a list of traffic cameras.

    To use, specify:
     - 'allowed_domains': mandatory parameter
     - 'operators': mandatory parameter, a dictionary mapping operator codes
                    to a tuple of operator name, operator Wikidata item and
                    state.
    """

    operators: dict[tuple[str, str, str]] = {}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url="https://" +  self.allowed_domains[0] + '/List/GetData/Cameras?query={"columns":[{"data":null,"name":""},{"name":"sortId","s":true},{"name":"state","s":true},{"name":"roadway","s":true},{"name":"description1"},{"data":5,"name":""}],"order":[{"column":2,"dir":"asc"},{"column":1,"dir":"asc"}],"start":0,"length":100,"search":{"value":""}}&lang=en-US')

    def parse(self, response: Response) -> Iterable[JsonRequest | Feature]:
        for start in range(100, response.json()["recordsFiltered"], 100):
            yield JsonRequest(
                url=response.url.replace("%22start%22:0", "%22start%22:{}".format(start)), callback=self.parse_cameras
            )
        yield from self.parse_cameras(response)

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        for camera in response.json()["data"]:
            properties = {
                "ref": camera["id"],
                "name": camera["displayName"],
                "lat": camera["latitude"],
                "lon": camera["longitude"],
                "operator": self.operators[camera["agencyName"]][0],
                "operator_wikidata": self.operators[camera["agencyName"]][1],
                "state": self.operators[camera["agencyName"]][2],
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            properties["extras"]["contact:webcam"] = "https://{}/tooltip/Cameras/{}".format(
                self.allowed_domains[0],
                properties["ref"]
            )
            properties["extras"]["camera:type"] = "fixed"
            yield Feature(**properties)
