import json
from base64 import b64encode
from typing import Iterable

import scrapy
from pygeohash import encode

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids


class A101TRSpider(scrapy.Spider):
    # TODO: due to a hard limit of 20 locations per request
    #       the spider is giving an incomplete output,
    #       5k locations instead of 13k.
    name = "a101_tr"
    item_attributes = {"brand": "A101", "brand_wikidata": "Q6034496"}
    requires_proxy = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self) -> Iterable[scrapy.Request]:
        for lat, lon in country_iseadgg_centroids("TR", 24):
            data = {"geoHash": encode(lat, lon, precision=9)}
            data = b64encode(json.dumps(data).encode("utf-8"))
            data = data.decode("utf-8")  # convert bytes back to string
            url_template = "https://rio.a101.com.tr/dbmk89vnr/CALL/StoreContentManager/nearestStores/default?__culture=tr-TR&__platform=web&data={}&__isbase64=true"
            yield scrapy.Request(url=url_template.format(data), callback=self.parse)

    def parse(self, response):
        for poi in response.json().get("stores", []):
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
