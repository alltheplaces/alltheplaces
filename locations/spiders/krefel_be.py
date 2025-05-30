from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST
from urllib.parse import urljoin


class KrefelBESpider(Spider):
    name = "krefel_be"
    item_attributes = {"brand": "Krëfel", "brand_wikidata": "Q3200093"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST}
    requires_proxy = True

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://api.krefel.be/occ/v2/krefel/stores?fields=STORE_FINDER&pageSize=1000&lang=nl")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["ref"] = store["krefelId"]
            item["website"] = urljoin("https://www.krefel.be/nl/winkels", store["name"])
            yield item
