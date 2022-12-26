import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class CoffeeTimeSpider(scrapy.Spider):
    name = "coffeetime"
    item_attributes = {"brand": "Coffee Time"}
    allowed_domains = ["www.coffeetime.com"]
    start_urls = ["https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token=YDGUJSNDOUAFKPRL"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data.get("store_info"))
            item["ref"] = data.get("store_info", {}).get("corporate_id")
            item["website"] = f'https://{self.allowed_domains[0]}{data.get("llp_url")}'

            oh = OpeningHours()
            for day in data.get("store_info", {}).get("store_hours").split(";")[:-1]:
                info_day = day.split(",")
                oh.add_range(
                    day=DAYS[int(info_day[0]) - 1],
                    open_time=info_day[1],
                    close_time=info_day[2],
                    time_format="%H%M",
                )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
