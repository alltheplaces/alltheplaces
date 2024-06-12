from urllib.parse import urlparse

import chompjs
from scrapy import Request, Spider

from locations.hours import DAYS_CN, OpeningHours, day_range
from locations.items import Feature


class SonyTWSpider(Spider):
    name = "sony_tw"
    item_attributes = {"brand": "Sony", "brand_wikidata": "Q41187"}
    start_urls = [
        "https://store.sony.com.tw/channelStore/index?area=all&productId=&type=direct&isType=Y",
        "https://store.sony.com.tw/channelStore/index?area=all&productId=&type=special&isType=Y&max=100",
    ]

    def parse(self, response):
        stores = response.xpath('//figure[@class="cell store__list"]')
        for store in stores:
            item = {}

            # Ref
            item["ref"] = store.xpath("./a/@href").get()
            item["website"] = f"https://{urlparse(response.request.url).netloc}{item['ref']}"

            # Name
            item["name"] = store.xpath('./a/div/p[@class="h5"]/strong/text()').get()

            # Address, Phone, Opening Hours
            # info_keys = store.xpath('./a/div/p[@class="h6"]/strong/text()').getall()
            info_values = store.xpath('./a/div/p[@class="text-gary"]').getall()
            for index in range(0, len(info_values)):
                info_values[index] = info_values[index].replace('<p class="text-gary">', "").replace("</p>", "")
                info_values[index] = (
                    info_values[index].replace("<br>", ",").replace("\n", "").replace("\t", "").replace(" ", "")
                )
            item["addr_full"] = info_values[0]
            item["phone"] = info_values[1].split("(")[0]
            self.parse_opening_hours(item, info_values[2][:-1])

            yield Request(url=item["website"], callback=self.parse_lat_lon, cb_kwargs={"item": item})

    def parse_opening_hours(self, item, hours):
        try:
            item["opening_hours"] = OpeningHours()
            for hour in hours.split(","):
                if "例假日" in hour:  # Holidays
                    continue
                elif "平日" in hour:  # Weekdays
                    day_range_start = "Mo"
                    day_range_end = "Fr"
                elif "週末" in hour:  # Weekends
                    day_range_start = "Sa"
                    day_range_end = "Su"
                else:
                    day_range_start = DAYS_CN.get(hour.split("~")[0])
                    day_range_end = DAYS_CN.get(hour.split(":", 1)[0].split("~")[1])
                if not day_range_start or not day_range_end:
                    continue
                days = day_range(day_range_start, day_range_end)
                open_time = hour.split(":", 1)[1].split("~")[0]
                close_time = hour.split(":", 1)[1].split("~")[1]
                item["opening_hours"].add_days_range(days, open_time, close_time)
        except Exception:
            self.crawler.stats.inc_value("failed_hours_parse")

    def parse_lat_lon(self, response, item):
        script = response.xpath('//script[contains(text(), "var uluru")]/text()').get()
        var_uluru = script[script.find("{", script.find("var uluru")) : script.find("}", script.find("var uluru")) + 1]
        var_uluru_json = chompjs.parse_js_object(var_uluru)
        item["lat"] = var_uluru_json["lat"]
        item["lon"] = var_uluru_json["lng"]

        yield Feature(**item)
