import scrapy
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TetaCZSpider(Spider):
    name = "teta_cz"
    item_attributes = {"brand": "Teta", "brand_wikidata": "Q20860823"}
    start_urls = ["https://www.tetadrogerie.cz/prodejny"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response, **kwargs):
        yield JsonRequest(
            url="https://www.tetadrogerie.cz/CMSPages/Sprinx/MapData.ashx",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=r"search=%7B%22Extra%22%3A%5B%5D%2C%22Services%22%3A%5B%5D%2C%22CosmeticsBrands%22%3A%5B%5D%2C%22Location%22%3A%7B%22Lat%22%3A0%2C%22Lng%22%3A0%7D%7D",
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)

            yield scrapy.Request(
                "https://www.tetadrogerie.cz/CMSPages/Sprinx/ShopDetail.aspx?id=%d" % location["Id"],
                callback=self.parse_location,
                cb_kwargs={"item": item},
            )

    def parse_location(self, response, **kwargs):
        item = kwargs["item"]

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
