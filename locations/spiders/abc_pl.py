from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AbcPLSpider(Spider):
    name = "abc_pl"

    def start_requests(self):
        yield JsonRequest(url="https://sklepyabc.pl/wp-content/themes/abc/api/js/gps.json")

    def parse(self, response, **kwargs):
        for feature in response.json()["shops"]:
            item = DictParser.parse(feature)
            item["ref"] = feature["idCRM"]
            item["housenumber"] = feature["number"]
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
