import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class FarmersHomeFurnitureSpider(scrapy.Spider):
    name = "farmers_home_furniture"
    item_attributes = {
        "brand": "Farmers Home Furniture",
        "brand_wikidata": "Q121586393",
        "country": "US",
    }
    allowed_domains = ["www.farmershomefurniture.com"]
    start_urls = ["https://www.farmershomefurniture.com/store-list.inc"]

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

                store_link = store.xpath("./@onclick").re_first("/stores/[0-9a-z-]+.inc")
                store_url = f"https://www.farmershomefurniture.com{store_link}"

                yield scrapy.Request(store_url, callback=self.parse_store, cb_kwargs=properties)

    def parse_store(self, response, city, state, address, phone):
        opening_hours = OpeningHours()
        store_hours = response.xpath('//div[@class="workspacearea"]/div/div/p/text()').extract()[2:]

        for hours in store_hours:
            if "closed" in hours.lower():
                continue
            hours = hours.strip()
            if m := re.match(r"(\w{3}):\s?(\d+)(:\d+)?(AM|PM)?-(\d+)(:\d+)?(AM|PM)?", hours):
                (
                    day,
                    start_hour,
                    start_min,
                    start_ampm,
                    end_hour,
                    end_min,
                    end_ampm,
                ) = m.groups()
                opening_hours.add_range(
                    day=day,
                    open_time=start_hour + (start_min or ":00") + (start_ampm or "AM"),
                    close_time=end_hour + (end_min or ":00") + (end_ampm or "PM"),
                    time_format="%I:%M%p",
                )

        store_coordinates = response.xpath("//script/text()").re_first("lat .*[\n].*").split(";")[:2]

        properties = {
            "street_address": address,
            "city": city,
            "phone": phone,
            "state": state,
            "lat": store_coordinates[0].split('"')[1],
            "lon": store_coordinates[1].split('"')[1],
            "opening_hours": opening_hours.as_opening_hours(),
            "ref": re.search(r".+/(.+?)/?(?:\.inc|$)", response.url).group(1),
            "website": response.url,
        }

        yield Feature(**properties)
