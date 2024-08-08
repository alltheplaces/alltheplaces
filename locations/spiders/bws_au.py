from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class BwsAUSpider(Spider):
    name = "bws_au"
    item_attributes = {"brand": "BWS", "brand_wikidata": "Q4836848"}
    allowed_domains = ["store.bws.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        for state in ["ACT", "NSW", "QLD", "SA", "VIC", "TAS", "WA", "NT"]:
            yield JsonRequest(
                "https://api.bws.com.au/apis/ui/StoreLocator/Stores/bws?state={}&type=allstores&Max=5000".format(state)
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["StoreNo"]
            slug = "{}-{}-{}".format(location["State"], location["Suburb"].replace(" ", "-"), item["ref"])
            item["website"] = urljoin("https://bws.com.au/storelocator/", slug.lower())

            # TODO: TradingHours

            yield item
