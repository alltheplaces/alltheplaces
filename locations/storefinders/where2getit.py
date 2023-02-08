import pprint

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature


class Where2GetItSpider(Spider):
    custom_settings = {"ROBOTSTXT_OBEY": False}

    w2gi_api = "https://hosted.where2getit.com/rest/locatorsearch"
    w2gi_id = ""
    w2gi_query = None
    request_size = 1000

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.w2gi_api,
            data={
                "request": {
                    "appkey": self.w2gi_id,
                    "formdata": {
                        "dataview": "store_default",
                        "limit": self.request_size,
                        "offset": offset,
                        "geolocs": {"geoloc": [{"addressline": "US"}]},
                        "searchradius": "5000",
                        "where": self.w2gi_query,
                    },
                }
            },
            meta={"offset": offset},
        )

    def start_requests(self):
        yield self.make_request(0)

    def parse(self, response, **kwargs):
        pprint.pp(response.json())
        if response.json()["response"]["collectioncount"] == self.request_size:
            yield self.make_request(response.meta["offset"] + self.request_size)

        for location in response.json()["response"]["collection"]:
            item = DictParser.parse(location)
            item["ref"] = location["clientkey"]

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
