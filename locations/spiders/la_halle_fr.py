from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST


class LaHalleFRSpider(Spider):
    name = "la_halle_fr"
    item_attributes = {"brand": "La Halle", "brand_wikidata": "Q100728296"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.lahalle.com/on/demandware.store/Sites-LHA_FR_SFRA-Site/fr_FR/Stores-FindStores?showMap=true&lat=48.85349504454055&long=2.3483914659676657&radius=10000",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            store["street-address"] = merge_address_lines([store.pop("address1", ""), store.pop("address2", "")])
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            yield item
