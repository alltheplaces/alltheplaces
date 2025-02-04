from typing import Iterable, Any

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class TheBodyShopSpider(scrapy.Spider):
    name = "the_body_shop"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}

    def start_requests(self) -> Iterable[Request]:
        for country in ["uk","es","au","ca","de","sg","dk","se","nl","fr","pt","at"]:
            yield JsonRequest(url= "https://api.thebodyshop.com/rest/v2/thebodyshop-{}/stores?fields=FULL&pageSize=1000".format(country),callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item.pop("name")
            item["website"] = store["canonicalUrl"]
            item["branch"] = store["displayName"]
            if store.get("region"):
                item["state"] = store["region"]["name"]
            yield item
