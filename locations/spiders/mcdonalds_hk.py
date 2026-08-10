from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsHKSpider(Spider):
    name = "mcdonalds_hk"
    item_attributes = McdonaldsSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT, "DOWNLOAD_TIMEOUT": 180}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.mcdonalds.com.hk/wp-admin/admin-ajax.php?action=get_restaurants", formdata={"type": "init"}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for index, store in enumerate(response.json()["restaurants"]):
            item = DictParser.parse(store)
            item["branch"] = store["title"]
            item["name"] = self.item_attributes["brand"]
            item["ref"] = index
            yield item
