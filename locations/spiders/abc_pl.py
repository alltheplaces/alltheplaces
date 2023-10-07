from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class ABCPLSpider(Spider):
    name = "abc_pl"
    item_attributes = {"brand": "abc", "brand_wikidata": "Q11683985"}

    def start_requests(self):
        yield JsonRequest(url="https://sklepyabc.pl/wp-content/themes/abc/api/js/gps.json")

    def parse(self, response, **kwargs):
        for feature in response.json()["shops"]:
            item = DictParser.parse(feature)
            item["ref"] = feature["idCRM"]
            item["housenumber"] = feature["number"]
            yield item
