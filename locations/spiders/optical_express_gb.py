from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class OpticalExpressGBSpider(Spider):
    name = "optical_express_gb"
    item_attributes = {"brand": "Optical Express", "brand_wikidata": "Q7098810", "country": "GB"}
    start_urls = ["https://www.opticalexpress.co.uk/Umbraco/Api/Clinics/Get?id=6929"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["website"] = location["page_url"]
            item["branch"] = location["clinic"]

            yield item
