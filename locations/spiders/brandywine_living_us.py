import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BrandywineLivingUSSpider(scrapy.Spider):
    name = "brandywine_living_us"
    start_urls = ["https://www.brandycare.com/company/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"locations\":(\[.*\])},\"locationData",
            response.xpath('//*[contains(text(),"postal_code")]/text()').get().replace("\\", ""),
        ).group(1)
        for location in json.loads(raw_data):
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["street_address"] = location["address_1"]
            item["website"] = "https://www.brandycare.com/community/" + item["name"].lower().replace(
                "community - ", ""
            ).replace(" ", "-")
            item["ref"] = location["communityid"]
            apply_category(Categories.NURSING_HOME, item)

            yield item
