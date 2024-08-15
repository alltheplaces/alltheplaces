import json
from base64 import b64encode
from typing import Iterable

import scrapy
from pygeohash import encode

from locations.dict_parser import DictParser
from locations.geo import city_locations


class A101TRSpider(scrapy.Spider):
    # TODO: due to a hard limit of 20 locations per request
    #       the spider is giving an incomplete output,
    #       5k locations instead of 13k.
    name = "a101_tr"
    item_attributes = {"brand": "A101", "brand_wikidata": "Q6034496"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        for city in city_locations("TR"):
            data = {"geoHash": encode(city.get("latitude"), city.get("longitude"), precision=5)}
            data = b64encode(json.dumps(data).encode("utf-8"))
            data = data.decode("utf-8")  # convert bytes back to string
            self.logger.info(f"{data}")
            url_template = "https://api-bp.a101prod.retter.io/dbmk89vnr/CALL/StoreContentManager/nearestStores/default?__culture=tr-TR&__platform=web&data={}&__isbase64=true"
            # TODO: /dbmk89vnr/ part of the url may not be constant
            yield scrapy.Request(url=url_template.format(data), callback=self.parse)

    def parse(self, response):
        for poi in response.json().get("stores", []):
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full")
            yield item
