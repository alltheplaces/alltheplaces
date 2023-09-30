from urllib.parse import urljoin

from scrapy import Spider

from locations.dict_parser import DictParser


class DanielsJewelersUSSpider(Spider):
    name = "daniels_jewelers_us"
    item_attributes = {"brand": "Daniel's Jewelers", "brand_wikidata": "Q120763875"}
    start_urls = ["https://admin.danielsjewelers.com/storelocator/index/stores/?type=all"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["storesjson"]:
            item = DictParser.parse(location)
            item["ref"] = location["storelocator_id"]
            item["website"] = urljoin("https://www.danielsjewelers.com/stores/", location["rewrite_request_path"])
            item["image"] = urljoin("https://admin.danielsjewelers.com/media/", location["path"])

            yield item
