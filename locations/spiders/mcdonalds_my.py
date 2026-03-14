from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsMYSpider(Spider):
    name = "mcdonalds_my"
    item_attributes = McdonaldsSpider.item_attributes

    async def start(self) -> AsyncIterator[FormRequest]:
        form_data = {
            "action": "get_nearby_stores",
            "distance": "100000",
            "lat": "4",
            "lng": "101",
            "ajax": "1",
        }
        yield FormRequest(
            url="https://www.mcdonalds.com.my/storefinder/index.php",
            method="POST",
            formdata=form_data,
            callback=self.parse,
        )

    def parse(self, response):
        for index, store in enumerate(response.json()["stores"]):
            item = DictParser.parse(store)
            item["ref"] = index
            yield item
