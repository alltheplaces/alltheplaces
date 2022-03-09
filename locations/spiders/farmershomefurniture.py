# -*- coding: utf-8 -*-
import re

import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAYS = {"0": "Mo", "1": "Tu", "2": "We", "3": "Th", "4": "Fr", "5": "Sa", "6": "Su"}


class FarmersHomeFurnitureSpider(scrapy.Spider):
    name = "farmershomefurniture"
    item_attributes = {"brand": "Farmers Home Furniture"}
    allowed_domains = ["www.farmershomefurniture.com"]
    start_urls = ["https://www.farmershomefurniture.com/store-list.inc"]
    download_delay = 1
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/63.0.3239.84 Safari/537.36"
    }

    def parse(self, response):
        for store in response.xpath("//tr"):
            store_data = store.xpath("./td/text()").getall()
            if store_data:
                properties = {
                    "city": store_data[0],
                    "state": store_data[1],
                    "address": store_data[2],
                    "phone": store_data[3],
                }

                store_link = store.xpath("./@onclick").re_first(
                    "/stores/[0-9a-z-]+.inc"
                )
                store_url = "https://www.farmershomefurniture.com/{}".format(store_link)

                yield scrapy.Request(
                    store_url, callback=self.parse_store, cb_kwargs=properties
                )

    def parse_store(self, response, city, state, address, phone):
        opening_hours = OpeningHours()
        store_hours = response.xpath(
            '//div[@class="workspacearea"]/div/div/p/text()'
        ).extract()[2:]

        for hours in store_hours:
            day, time = hours.strip().split(":")
            if day != "Sun":
                time_range = time.split("-")
                if time_range[0] != "Closed":
                    opening_hours.add_range(
                        day=day[:2],
                        open_time=time_range[0].strip() + ":00",
                        close_time=time_range[1].strip() + ":00",
                    )

        store_coordinates = (
            response.xpath("//script/text()").re_first("lat .*[\n].*").split(";")[:2]
        )

        properties = {
            "addr_full": address,
            "city": city,
            "phone": phone,
            "state": state,
            "lat": store_coordinates[0].split('"')[1],
            "lon": store_coordinates[1].split('"')[1],
            "opening_hours": opening_hours.as_opening_hours(),
            "ref": re.search(r".+/(.+?)/?(?:\.inc|$)", response.url).group(1),
        }

        yield GeojsonPointItem(**properties)
