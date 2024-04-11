from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class VirtualEarthSpider(Spider):
    dataset_attributes = {"source": "api", "api": "virtualearth.net"}

    dataset_id = ""
    dataset_name = ""
    key = ""

    filter = "Adresstyp Eq 1"
    select = "*"

    page_size = 250

    def start_requests(self):
        yield JsonRequest(
            url=f"https://spatial.virtualearth.net/REST/v1/data/{self.dataset_id}/{self.dataset_name}?key={self.key}&$filter={self.filter}&$select={self.select}&$format=json&$top=1&$inlinecount=allpages",
            callback=self.pages,
        )

    def pages(self, response, **kwargs):
        total_count = int(response.json()["d"]["__count"])
        offset = 0

        while offset < total_count:
            yield JsonRequest(
                url=f"https://spatial.virtualearth.net/REST/v1/data/{self.dataset_id}/{self.dataset_name}?key={self.key}&$filter={self.filter}&$select={self.select}&$format=json&$top={self.page_size}&$skip={offset}",
            )
            offset += self.page_size

    def parse(self, response, **kwargs):
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

    def parse_item(self, item, feature, **kwargs):
        yield item
