import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class SupervaluIESpider(Spider):
    name = "supervalu_ie"
    item_attributes = {"brand": "SuperValu", "brand_wikidata": "Q7642081"}
    start_urls = ["https://supervalu.ie/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"stores: (\[.+\]),", response.text).group(1)):
            if location["publish"] != 1:
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["title"]
            item["phone"] = location["telephone"]
            item["email"] = location["email"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["extras"]["check_date"] = location["modified"]
            item["street_address"] = merge_address_lines(
                [location["address_line_1"], location["address_line_2"], location["address_line_3"]]
            )
            item["postcode"] = location["address_post_code"]
            item["city"] = location["address_city"]
            item["state"] = location["address_county"]

            yield item
