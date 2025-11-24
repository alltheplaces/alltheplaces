from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class YoungsGBSpider(scrapy.Spider):
    name = "youngs_gb"
    item_attributes = {"brand": "Young's", "brand_wikidata": "Q8057802"}
    start_urls = ["https://www.youngs.co.uk/wp-json/wp/v2/venues?page=1&per_page=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            data = location.get("acf", {})
            if not data:
                continue

            item = DictParser.parse(data)
            item["ref"] = data.get("siteId")
            item["website"] = (
                data.get("pubExternalUrl").replace("https://https://", "https://").replace("http://", "https://")
            )
            item["branch"] = data.get("venueName")
            item["addr_full"] = merge_address_lines([item["city"], item["postcode"]])
            lon = item.get("lon", "")
            if isinstance(lon, str):
                lon_clean = lon.replace(",", "").replace(" ", "")
                if lon_clean == "BA15LS":
                    item["lon"] = data.get("postcode")
                    item["postcode"] = data.get("longitude")
                else:
                    item["lon"] = lon_clean

            yield item
