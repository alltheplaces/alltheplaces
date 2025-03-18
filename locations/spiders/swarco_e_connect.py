from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SwarcoEConnectSpider(Spider):
    name = "swarco_e_connect"
    item_attributes = {"operator": "Swarco", "operator_wikidata": "Q118383410"}
    start_urls = ["https://swarcoeconnect.org/evolt-map/marker-list.php"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if not location["visible"]:
                continue
            item = DictParser.parse(location)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
