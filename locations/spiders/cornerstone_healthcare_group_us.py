import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CornerstoneHealthcareGroupUSSpider(Spider):
    name = "cornerstone_healthcare_group_us"
    item_attributes = {"brand": "Cornerstone Healthcare Group"}
    start_urls = ["https://www.cornerstonehospitals.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//@data-markers-list").get()):
            item = DictParser.parse(location)
            item["website"] = item["ref"] = location["locationPagePath"]
            apply_category(Categories.HOSPITAL, item)
            yield item
