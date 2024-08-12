from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class VirtualEarthSpider(Spider):
    """
    A virtual earth spider is typically data hosted via virtualearth.net as a JSON API.

    Spiders using this will likely migrate to other means in the near future.

    > Free (Basic) account customers can continue to use Bing Maps Spatial Data Service Query API until June 30th, 2025.
    > Enterprise account customers can continue to use Bing Maps Spatial Data Service Query API until June 30th, 2028.

    See https://learn.microsoft.com/en-us/bingmaps/spatial-data-services/query-api/

    To use, specify:
      - `dataset_id`: mandatory parameter
      - `dataset_name`: mandatory parameter
      - `api_key`: mandatory parameter
      - `dataset_filter`: optional parameter, default value is "Adresstyp Eq 1"
      - `dataset_select`: optional parameter, default valus is "*"
      - `page_size`: optional parameter, default value is 250
    """

    dataset_attributes = {"source": "api", "api": "virtualearth.net"}

    dataset_id = ""
    dataset_name = ""
    api_key = ""
    dataset_filter = "Adresstyp Eq 1"
    dataset_select = "*"

    page_size = 250

    def start_requests(self):
        yield JsonRequest(
            url=f"https://spatial.virtualearth.net/REST/v1/data/{self.dataset_id}/{self.dataset_name}?key={self.api_key}&$filter={self.dataset_filter}&$select={self.dataset_select}&$format=json&$top=1&$inlinecount=allpages",
            callback=self.pages,
        )

    def pages(self, response, **kwargs):
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

    def parse_item(self, item, feature, **kwargs):
        yield item
