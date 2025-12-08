from typing import Any

from chompjs import parse_js_object
from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class SolaSalonStudiosSpider(Spider):
    name = "sola_salon_studios"
    item_attributes = {"brand": "Sola Salons", "brand_wikidata": "Q64337426"}
    allowed_domains = ["platform.solasalonstudios.com", "www.solasalonstudios.com"]
    start_urls = ["https://platform.solasalonstudios.com/v1/get-web-locations-list?country=all&sola-demo=false"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state in response.json()["data"]:
            for location in state["locations"]:
                item = DictParser.parse(location)
                item["website"] = "https://www.solasalonstudios.com/locations/" + location["url_name"]
                yield Request(url=item["website"], meta={"item": item}, callback=self.add_address_details)

    def add_address_details(self, response: Response) -> Any:
        location_js = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        location = parse_js_object(location_js)["props"]["pageProps"]["locationSEODetails"]["data"]
        item = response.meta["item"]
        item["street_address"] = clean_address([location["address_1"], location["address_2"]])
        item["country"] = location["country"]
        yield item
