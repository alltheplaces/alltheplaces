import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class NemzetiDohanyboltHUSpider(scrapy.Spider):
    name = "nemzeti_dohanybolt_hu"
    allowed_domains = ["nemzetidohany.hu"]
    item_attributes = {"brand_wikidata": "Q20639040"}

    def start_requests(self):
        params = {
            "filter": {"date": None, "products": None, "search": ""},
            "poi_only": True,
            "lat": 47.1617435,
            "lng": 19.5057541,
        }
        yield JsonRequest("https://nemzetidohany.hu/publicapi/trafik/search", data=params)

    def parse(self, response):
        for poi in response.json().get("data", []):
            yield DictParser.parse(poi)
