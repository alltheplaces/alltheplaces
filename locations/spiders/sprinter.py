from typing import Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import FIREFOX_LATEST


class SprinterSpider(JSONBlobSpider):
    name = "sprinter"
    SPRINTER = {"brand": "Sprinter", "brand_wikidata": "Q6133465"}
    SPORT_ZONE = {"brand": "Sport Zone", "brand_wikidata": "Q18485899"}
    locations_key = "stores"
    user_agent = FIREFOX_LATEST

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        yield JsonRequest(
            url="https://www.sprintersports.com/api/store/by_points",
            method="POST",
            body=b'{"p1x":-180,"p2y":90,"p2x":180,"p1y":-90,"clat":1,"clon":1}',
            headers={"Referer": "https://www.sprintersports.com/tiendas"},
        )
        yield JsonRequest(
            url="https://www.sprintersports.com/pt/api/store/by_points",
            method="POST",
            body=b'{"p1x":-180,"p2y":90,"p2x":180,"p1y":-90,"clat":1,"clon":1}',
            headers={"Referer": "https://www.sprintersports.com/pt/lojas"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["active"] is True:
            item["branch"] = item.pop("name").replace("Sprinter ", "").replace("Sport Zone ", "")
            item["street_address"] = item.pop("addr_full")

            if not item["website"].startswith("http"):
                item["website"] = "https://{}".format(item["website"])

            if feature["id_market"] == 2:
                item.update(self.SPORT_ZONE)
            elif feature["id_market"] == 1:
                item.update(self.SPRINTER)

            yield item
