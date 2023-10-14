import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class NemzetiDohanyboltHuSpider(scrapy.Spider):
    name = "nemzeti_dohanybolt_hu"
    allowed_domains = ["nemzetidohany.hu"]
    item_attributes = {"brand": "Nemzeti Dohánybolt", "brand_wikidata": "Q20639040"}

    def start_requests(self):
        params = {
            "filter": {"date": None, "products": None, "search": ""},
            "poi_only": True,
            "lat": 47.1617435,
            "lng": 19.5057541,
        }
        yield JsonRequest("https://nemzetidohany.hu/publicapi/trafik/search", data=params)

    def parse(self, response):
        pois = response.json().get("data")
        for poi in pois:
            yield DictParser.parse(poi)
