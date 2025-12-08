from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsHKSpider(Spider):
    name = "mcdonalds_hk"
    item_attributes = McdonaldsSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[FormRequest]:
        url = "https://www.mcdonalds.com.hk/wp-admin/admin-ajax.php?action=get_restaurants"
        yield FormRequest(url=url, formdata={"type": "init"}, method="POST")

    def parse(self, response):
        for index, store in enumerate(response.json()["restaurants"]):
            item = DictParser.parse(store)
            item["name"] = "McDonald's " + store["title"]
            item["country"] = "HK"
            item["ref"] = index
            yield item
