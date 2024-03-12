from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.items import Feature


class VirtualEarthSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "virtualearth.net"}
    dataset_id = ""
    dataset_name = ""
    api_key = ""
    dataset_filter = "Adresstyp Eq 1"
    dataset_select = "*"
    page_size = 250
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/spatial\.virtualearth\.net\/REST\/v1\/data\/(?P<dataset_id>[0-9a-f]{32})\/(?P<dataset_name>[^?]+)\?.*?(?<=[?&])\$filter=(?P<dataset_filter>[^&]+)&.*?(?<=&)\$select=(?P<dataset_select>[^&]+)&.*?(?<=&)key=(?P<api_key>[^&]+)(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/spatial\.virtualearth\.net\/REST\/v1\/data\/(?P<dataset_id>[0-9a-f]{32})\/(?P<dataset_name>[^?]+)\?.*?(?<=[?&])\$select=(?P<dataset_select>[^&]+)&.*?(?<=&)\$filter=(?P<dataset_filter>[^&]+)&.*?(?<=&)key=(?P<api_key>[^&]+)(?:&|$)"
        ),
    ]

    def start_requests(self):
        yield JsonRequest(
            url=f"https://spatial.virtualearth.net/REST/v1/data/{self.dataset_id}/{self.dataset_name}?key={self.api_key}&$filter={self.dataset_filter}&$select={self.dataset_select}&$format=json&$top=1&$inlinecount=allpages",
            callback=self.pages,
        )

    def pages(self, response: Response):
        total_count = int(response.json()["d"]["__count"])
        offset = 0

        while offset < total_count:
            yield JsonRequest(
                url=f"https://spatial.virtualearth.net/REST/v1/data/{self.dataset_id}/{self.dataset_name}?key={self.api_key}&$filter={self.dataset_filter}&$select={self.dataset_select}&$format=json&$top={self.page_size}&$skip={offset}",
            )
            offset += self.page_size

    def parse(self, response: Response):
        for feature in response.json()["d"]["results"]:
            feature["ref"] = feature.get("EntityID")
            feature["address"] = {
                "street_address": feature.get("AddressLine"),
                "city": feature.get("Locality"),
                "state": feature.get("AdminDistrict"),
                "post_code": feature.get("PostalCode"),
                "country": feature.get("CountryRegion"),
            }

            item = DictParser.parse(feature)

            yield from self.parse_item(item, feature) or []

    def parse_item(self, item: Feature, feature: dict):
        yield item
