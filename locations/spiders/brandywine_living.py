import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BrandywineLivingSpider(scrapy.Spider):
    name = "brandywine_living"
    start_urls = ["https://www.brandycare.com/company/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"locations\":(\[.*\])},\"locationData",
            response.xpath('//*[contains(text(),"addresscity")]/text()').get().replace("\\", ""),
        ).group(1)
        for location in json.loads(raw_data):
            item = DictParser.parse(location)
            item["ref"] = location["communityid"]
            item["lat"] = location["addresslatitude"]
            item["lon"] = location["addresslongitude"]

            apply_category(Categories.NURSING_HOME, item)

            yield item
