from typing import AsyncIterator

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class A1HRSpider(Spider):
    name = "a1_hr"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q688755"}
    allowed_domains = ["www.a1.hr"]
    start_urls = [
        "https://www.a1.hr/prodajna-mjesta?p_p_id=pos_WAR_pos&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=searchPos&p_p_cacheability=cacheLevelPage"
    ]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(
                url=url,
                body="query=&tipprikaza=lista&types=center&types=partner",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST",
            )

    def parse(self, response):
        for location in response.json()["result"]:
            if location["type"] != "center":
                # type="partner" should be ignored.
                continue
            item = DictParser.parse(location)
            if location.get("branchId"):
                item["ref"] = location["branchId"]
            item["name"] = location["location"]
            item["street_address"] = item.pop("addr_full", None)
            item["opening_hours"] = OpeningHours()
            for day_name, hours_range in location["workHours"].items():
                if day_name.title() not in DAYS_EN.keys():
                    continue
                if hours_range == "-":
                    # Closed
                    continue
                item["opening_hours"].add_range(DAYS_EN[day_name.title()], *hours_range.split("-", 1), "%H:%M")
            yield item
