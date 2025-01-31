import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingPESpider(Spider):
    name = "burger_king_pe"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    api_token = ""

    def start_requests(self):
        yield Request(
            url="https://www.burgerking.pe/carta/ver-todo",
            body='["accessToken"]',
            headers={"next-action": "2686d5940e3bce57deceb15dc1c5eb63d9a86f4c"},
            method="POST",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.api_token = re.search(r"1:\s*\"(.+)\"", response.text).group(1)
        yield JsonRequest(
            url="https://apiprod.pidelo.digital/api.stores/v1/stores/get-district?brandId=41",
            headers={"authorization": f"Bearer {self.api_token}"},
            callback=self.parse_districts,
        )

    def parse_districts(self, response: Response, **kwargs: Any) -> Any:
        for district in response.json()["data"]:
            yield JsonRequest(
                url=f'https://apiprod.pidelo.digital/api.stores/v1/stores/pickup?brandId=41&district={district["name"]}',
                headers={"authorization": f"Bearer {self.api_token}"},
                callback=self.parse_locations,
                cb_kwargs=dict(district=district["name"]),
            )

    def parse_locations(self, response: Response, district: str) -> Any:
        for location in response.json().get("data", []):
            location.update(location.pop("addressInformation"))
            item = DictParser.parse(location)
            item["housenumber"] = location.get("exteriorNumber")
            item["street"] = item.pop("addr_full").replace("S/N", "")
            item["addr_full"] = merge_address_lines([item["housenumber"], item["street"], district])
            yield item
