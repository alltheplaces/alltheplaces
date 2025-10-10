import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class RamsayHealthCareAUSpider(scrapy.Spider):
    name = "ramsay_health_care_au"
    item_attributes = {
        "operator": "Ramsay Health Care",
        "operator_wikidata": "Q17054333",
    }
    start_urls = ["https://www.ramsayhealth.com.au/en/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"\"results\":(\[.*\]),\"anchorId", response.xpath('//*[contains(text(),"longitude")]/text()').get()
        ).group(1)
        for location in json.loads(raw_data):
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
            item["website"] = location["href"]
            if location["locationTypeName"] == "Pharmacy":
                apply_category(Categories.PHARMACY, item)
            elif location["locationTypeName"] in ["Mental Health Clinic", "Psychology Clinic", "Ramsay Health Plus"]:
                apply_category(Categories.CLINIC, item)
            yield item
