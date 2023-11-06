import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class DairyQueenUSSpider(Spider):
    name = "dairy_queen_us"
    allowed_domains = ["prod-dairyqueen.dotcmscloud.com"]
    start_urls = ["https://prod-dairyqueen.dotcmscloud.com/api/es/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Missing robots.txt
    brands = {
        "Food and Treat": {
            "brand": "DQ Grill & Chill",
            "brand_wikidata": "Q1141226",
            "extras": {"cuisine": "ice_cream;burger"},
        },
        "Treat Only": {"brand": "Dairy Queen", "brand_wikidata": "Q1141226", "extras": {"cuisine": "ice_cream"}},
    }

    def start_requests(self):
        yield JsonRequest(
            url=self.start_urls[0],
            method="POST",
            headers={
                "Referer": "https://www.dairyqueen.com/",
            },
            data={"size": 10000, "query": {"bool": {"must": [{"term": {"contenttype": "locationDetail"}}]}}},
        )

    def parse(self, response):
        for location in response.json()["contentlets"]:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location.get("latlong", ",").split(",", 2)
            item.update(self.brands[location["conceptType"]])
            item["name"] = re.sub(r"^\d+ : ", "", item["name"])
            item["street_address"] = location.get("address3")
            item["website"] = "https://www.dairyqueen.com" + location.get("urlTitle")
            yield item
