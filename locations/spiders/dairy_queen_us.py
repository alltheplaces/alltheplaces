import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.dict_parser import DictParser


class DairyQueenUSSpider(Spider):
    name = "dairy_queen_us"
    allowed_domains = ["prod-dairyqueen.dotcmscloud.com"]
    start_urls = ["https://prod-dairyqueen.dotcmscloud.com/api/es/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Missing robots.txt
    item_attributes = {"nsi_id": "N/A"}
    brands = {
        "Food and Treat": {
            "brand": "DQ Grill & Chill",
            "brand_wikidata": "Q1141226",
            "extras": {"amenity": "fast_food", "cuisine": "ice_cream;burger"},
        },
        "Treat Only": {
            "brand": "Dairy Queen",
            "brand_wikidata": "Q1141226",
            "extras": {"amenity": "fast_food", "cuisine": "ice_cream"},
        },
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
            if location["conceptType"] in self.brands.keys():
                item["brand"] = self.brands[location["conceptType"]]["brand"]
                item["brand_wikidata"] = self.brands[location["conceptType"]]["brand_wikidata"]
                for tag_key, tag_value in self.brands[location["conceptType"]]["extras"].items():
                    apply_category({tag_key: tag_value}, item)
            item["branch"] = re.sub(r"^\d+ : ", "", item["name"])
            item["name"] = item["brand"]
            item["street_address"] = location.get("address3")
            item["website"] = "https://www.dairyqueen.com" + location.get("urlTitle")
            yield item
