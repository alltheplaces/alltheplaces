from scrapy import Spider

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

# To use this spider, specify one or more start_urls which have a domain of
# www.locally.com or brandname.locally.com and path of /stores/conversion_data
# Include all arguments in the URL.


class LocallySpider(Spider, AutomaticSpiderGenerator):
    custom_settings = {"ROBOTSTXT_OBEY": False}
    detection_rules = [
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/[A-Za-z0-9\-.]+\.locally\.com\/stores\/conversion_data\?.+)$"
        )
    ]

    def parse(self, response):
        for location in response.json()["markers"]:
            self.pre_process_item(location)
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                open = f"{day[:3].lower()}_time_open"
                close = f"{day[:3].lower()}_time_close"
                if not location.get(open) or len(str(location.get(open))) < 3:
                    continue
                item["opening_hours"].add_range(
                    day=day,
                    open_time=f"{str(location.get(open))[:-2]}:{str(location.get(open))[-2:]}",
                    close_time=f"{str(location.get(close))[:-2]}:{str(location.get(close))[-2:]}",
                )
            yield from self.post_process_item(item, location)

    def pre_process_item(self, location: dict):
        pass

    def post_process_item(self, item: Feature, location: dict):
        yield item
