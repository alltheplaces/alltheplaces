import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

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
    """

    allowed_domains: list[str] = []

    async def start(self) -> AsyncIterator[JsonRequest]:
        if len(self.allowed_domains) != 1:
            raise ValueError("Specify one domain name in the allowed_domains list attribute.")
            return
        yield JsonRequest(
            url="https://"
            + self.allowed_domains[0]
            + '/List/GetData/Cameras?query={"columns":[{"data":null,"name":""},{"name":"sortId","s":true},{"name":"state","s":true},{"name":"roadway","s":true},{"name":"description1"},{"data":5,"name":""}],"order":[{"column":2,"dir":"asc"},{"column":1,"dir":"asc"}],"start":0,"length":100,"search":{"value":""}}&lang=en-US'
        )

    def parse(self, response: TextResponse) -> Iterable[JsonRequest | Feature]:
        for start in range(100, response.json()["recordsFiltered"], 100):
            yield JsonRequest(
                url=response.url.replace("%22start%22:0", "%22start%22:{}".format(start)), callback=self.parse_cameras
            )
        yield from self.parse_cameras(response)

    def parse_cameras(self, response: TextResponse) -> Iterable[Feature]:
        for camera in response.json()["data"]:
            item = Feature()
            item["ref"] = str(camera["id"])
            item["name"] = camera["location"]
            item["state"] = camera["state"]
            wkt = camera["latLng"]["geography"]["wellKnownText"]
            if m := re.fullmatch(r"POINT \((-?\d+\.\d+) (-?\d+\.\d+)\)", wkt):
                item["lon"] = m.group(1)
                item["lat"] = m.group(2)
            apply_category(Categories.SURVEILLANCE_CAMERA, item)
            item["extras"]["contact:webcam"] = "https://{}/tooltip/Cameras/{}".format(
                self.allowed_domains[0], item["ref"]
            )
            item["extras"]["camera:type"] = "fixed"
            yield from self.post_process_item(item, response, camera) or []

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override to perform post-processing of the extracted feature."""
        yield item
