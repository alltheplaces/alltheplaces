import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.subway import SubwaySpider


class SubwaySGSpider(scrapy.Spider):
    name = "subway_sg"
    item_attributes = SubwaySpider.item_attributes
    start_urls = [
        "https://subwayisfresh.com.sg/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1",
    ]

    def parse(self, response, **kwargs):
        for store in response.json():
            store["opening_hours"] = store.pop("open_hours")
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day, time in eval(store["opening_hours"]).items():
                day = sanitise_day(day.title())
                for open_close_time in time:
                    open_time, close_time = open_close_time.split("-")
                    item["opening_hours"].add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                    )

            yield item
