import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class NextcareSpider(scrapy.Spider):
    name = "nextcare"
    item_attributes = {"brand": "NextCare Urgent Care", "brand_wikidata": "Q139994485"}
    allowed_domains = ["nextcare.com"]
    start_urls = ("https://nextcare.com/find-your-location/",)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_data = json.loads(
            re.search(
                r"locations_data\":(\[.*\]),\"ajax_url\"",
                response.xpath('//*[contains(text(),"zipcode")]/text()').get(),
            ).group(1)
        )
        for location in location_data:
            if location.get("brand") == "NextCare Urgent Care":
                item = DictParser.parse(location)
                item["branch"] = item.pop("name")
                item["ref"] = location.get("post_id")
                item["housenumber"] = location.get("aptsuit")
                item["street_address"] = item.pop("street")
                item["website"] = f"https://nextcare.com/locations/{item['state']}/{location.get('full_city')}/"
                apply_category(Categories.CLINIC_URGENT, item)
                yield item
