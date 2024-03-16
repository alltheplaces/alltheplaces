import json
from typing import Iterable

import scrapy
from scrapy import FormRequest, Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TetaCZSpider(Spider):
    name = "teta_cz"
    item_attributes = {"brand": "Teta", "brand_wikidata": "Q20860823"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            url="https://www.tetadrogerie.cz/CMSPages/Sprinx/MapData.ashx",
            formdata={
                "search": json.dumps(
                    {"Extra": [], "Services": [], "CosmeticsBrands": [], "Location": {"Lat": 0, "Lng": 0}}
                )
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["operator"] = item.pop("name")

            yield scrapy.Request(
                "https://www.tetadrogerie.cz/CMSPages/Sprinx/ShopDetail.aspx?id=%d" % location["Id"],
                callback=self.parse_location,
                cb_kwargs={"item": item},
            )

    def parse_location(self, response, **kwargs):
        item = kwargs["item"]

        item["website"] = response.urljoin(response.xpath('//a[@id="hpDetail"]/@href').get())
        item["addr_full"] = response.xpath('//h3[@class="sx-store-detail-small-info"]/text()').get().strip()

        item["opening_hours"] = OpeningHours()
        opening_time_days = response.xpath("//table[@class='sx-store-detail-small-opening']/tr/td[2]/text()")
        if len(opening_time_days) != 7:
            raise ValueError(f"number of opening time days must be 7, not {len(opening_time_days)!r}")
        for day, opening_time in zip(DAYS, opening_time_days):
            opening_time = opening_time.get().strip()
            if opening_time.strip().lower() == "zavřeno":
                continue
            for time_range in opening_time.split(","):
                open_time, close_time = time_range.split("-")
                item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), "%H:%M")

        yield item
