import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KFCITSpider(Spider):
    name = "kfc_it"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://www.kfc.it/ristoranti"]

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = json.loads(data_raw)["props"]["pageProps"]["data"]["items"]
        for store in locations:
            store.update(store.pop("labels"))
            item = DictParser.parse(store)
            yield item
