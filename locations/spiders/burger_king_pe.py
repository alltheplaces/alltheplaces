import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingPESpider(Spider):
    name = "burger_king_pe"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    api_token = ""
    start_urls = ["https://www.burgerking.pe/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Search for the desired JavaScript file
        yield response.follow(
            url=response.xpath("//script/@src").re(r"_next/static/chunks/\d{4}-\w+\.js")[-1],
            callback=self.parse_action_token,
        )

    def parse_action_token(self, response: Response, **kwargs: Any) -> Any:
        matches = re.findall(r"[a-z][\s=]+\(0,\s*o.\$\)\(\"([a-f0-9]{40})\"\)", response.text)
        action_token = matches[1] if len(matches) > 1 else matches[0]
        yield Request(
            url="https://www.burgerking.pe/",
            body='["accessToken"]',
            headers={"next-action": action_token},
            method="POST",
            callback=self.parse_request,
        )

    def parse_request(self, response: Response, **kwargs: Any) -> Any:
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
            item["name"] = None
            item["housenumber"] = location.get("exteriorNumber")
            item["street"] = item.pop("addr_full").replace("S/N", "")
            item["addr_full"] = merge_address_lines([item["housenumber"], item["street"], district])
            item["opening_hours"] = OpeningHours()
            for shift in location.get("hours", []):
                open_time = shift.get("startHour")
                close_time = shift.get("endHour")
                if open_time and close_time:
                    item["opening_hours"].add_days_range(DAYS, open_time, close_time)
            yield item
