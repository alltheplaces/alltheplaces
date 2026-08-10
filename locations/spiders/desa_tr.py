from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class DesaTRSpider(scrapy.Spider):
    name = "desa_tr"
    item_attributes = {
        "brand": "Desa",
        "brand_wikidata": "Q17513880",
    }
    start_urls = ["https://www.desa.com.tr/api/Store/GetStoriesLite"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["magazalar"]:
            if "desa" in location.get("tanim").lower():
                item = DictParser.parse(location)
                item["branch"] = (
                    location["tanim"].replace("Desa ", "").replace("DESA ", "").replace("-", "").replace("/", "")
                )
                item["phone"] = location["telefon"]
                item["state"] = location["il"]
                item["city"] = location["ilce"]
                item["street_address"] = location["adres"]
                yield item
