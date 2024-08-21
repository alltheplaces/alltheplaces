from typing import Any

import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser


class SausageSaloonZASpider(Spider):
    name = "sausage_saloon_za"
    item_attributes = {"brand": "Sausage Saloon", "brand_wikidata": "Q116619342"}

    def start_requests(self):
        form_data = {"action": "get_stores", "lat": "-29", "lng": "24", "radius": "10000000"}
        yield scrapy.http.FormRequest(
            url="https://www.sausagesaloon.co.za/wp-admin/admin-ajax.php",
            method="POST",
            formdata=form_data,
            callback=self.parse,
        )

    def parse(self, response, **kwargs: Any) -> Any:
        for index, location in response.json().items():
            item = DictParser.parse(location)
            item["name"] = location["na"]
            item["phone"] = location.get("te", "")
            item["street_address"] = location["st"]
            item["city"] = location["ct"]
            item["postcode"] = location["zp"]
            item["website"] = location["gu"]

            yield item
