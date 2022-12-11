from scrapy import Spider

from locations.dict_parser import DictParser


class BreWingzSpider(Spider):
    name = "bre_wingz"
    item_attributes = {"brand": "BreWingz"}
    start_urls = ["https://www.brewingz.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)

            item["name"] = store["store"]

            yield item
