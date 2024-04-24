from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class SamsClubMXSpider(Spider):
    name = "sams_club_mx"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}
    start_urls = ["https://www.sams.com.mx/rest/model/atg/userprofiling/ProfileActor/stateStoreLocator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for locations in response.json()["stateStores"].values():
            for location in locations:
                item = DictParser.parse(location)
                item["website"] = "https://www.sams.com.mx/clubes/{}".format(item["ref"])
                yield item
