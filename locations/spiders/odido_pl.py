from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class OdidoPLSpider(Spider):
    name = "odido_pl"
    item_attributes = {"brand": "Odido", "brand_wikidata": "Q106947294"}

    def start_requests(self):
        yield JsonRequest(url="https://www.sklepy-odido.pl/api/shops?itemsPerPage=10000")

    def parse(self, response, **kwargs):
        for feature in response.json()["data"]:
            item = DictParser.parse(feature)
            item["postcode"] = item["postcode"].strip()
            if "building" in feature:
                item["housenumber"] = feature["building"]
            item["ref"] = feature["index"]  # Unknown whether it's stable
            yield item
