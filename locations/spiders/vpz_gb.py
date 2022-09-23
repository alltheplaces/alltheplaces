from scrapy import Spider

from locations.dict_parser import DictParser


class VPZGB(Spider):
    name = "vpz_gb"
    item_attributes = {"brand": "VPZ", "brand_wikidata": "Q107300487", "country": "GB"}
    start_urls = [
        "https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/14072/stores.js"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)

            yield item
