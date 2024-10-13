from typing import Any
import json

from scrapy.spiders import Spider
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
#from urllib.parse import urljoin
from scrapy.http import Response

class WilkoGBSpider(Spider):
    name = "wilko_gb"
    item_attributes = {"brand": "Wilko", "brand_wikidata": "Q8002536"}
    start_urls = ["https://locator.uberall.com/api/storefinders/5Ixa2nvRqDhqc7H9r1AP68AJFTmO4n/locations/all?v=20230110&language=en-gb&fieldMask=id&fieldMask=identifier&fieldMask=googlePlaceId&fieldMask=lat&fieldMask=lng&fieldMask=name&fieldMask=country&fieldMask=city&fieldMask=province&fieldMask=streetAndNumber&fieldMask=zip&fieldMask=businessId&fieldMask=addressExtra&country=UK"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["locations"]:
            item = DictParser.parse(location)
            if "Collection" not in item["name"]:
                item["street_address"] = merge_address_lines([location["addressExtra"], location["streetAndNumber"]])
#                address=location["streetAndNumber"].replace(" ","-")
#                city=location["city"]
#                id=location["identifier"]
#                slug=city +"/"+ address +"/" +id
#                item["website"] = urljoin("https://www.wilko.com/en-uk/stores/l/", slug)

                yield item
