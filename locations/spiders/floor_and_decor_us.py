from typing import AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser


class FloorAndDecorUSSpider(Spider):
    name = "floor_and_decor_us"
    item_attributes = {"brand": "Floor & Decor", "brand_wikidata": "Q56280964"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[FormRequest]:
        for state in GeonamesCache().get_us_states().keys():
            yield FormRequest(
                url="https://www.flooranddecor.com/on/demandware.store/Sites-floor-decor-Site/default/Stores-GetStores?ajax=true",
                formdata={"dwfrm_storeLocator_search": state, "dwfrm_storeLocator_radius": "300"},
            )

    def parse(self, response):
        for store in response.json()["stores"]["storesList"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.flooranddecor.com/" + store.get("detailsLink")
            yield item
