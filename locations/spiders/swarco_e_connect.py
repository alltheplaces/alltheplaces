from scrapy import Spider

from locations.dict_parser import DictParser


class SwarcoEConnectSpider(Spider):
    name = "swarco_e_connect"
    item_attributes = {"brand": "Swarco E.Connect", "brand_wikidata": "Q118383410"}
    start_urls = ["https://swarcoeconnect.org/evolt-map/marker-list.php"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if not location["visible"]:
                continue
            yield DictParser.parse(location)
