import re

from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.calvin_klein import CalvinKleinSpider


class CalvinKleinAUSpider(Spider):
    name = "calvin_klein_au"
    item_attributes = CalvinKleinSpider.item_attributes
    start_urls = ["https://www.calvinklein.com.au/stores/index/dataAjax"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location["i"]
            item["lat"] = location["l"]
            item["lon"] = location["g"]
            item["name"] = location["n"]
            item["addr_full"] = merge_address_lines(location.get("a"))
            item["street_address"] = location["a"][0]
            item["city"] = location["a"][1]
            item["state"] = location["a"][2]
            item["postcode"] = location["a"][3]
            item["website"] = f'https://www.calvinklein.com.au{location["u"]}'
            item["phone"] = location["p"]
            item["email"] = location["e"]

            oh = OpeningHours()
            for rule in location["oh"].replace(" ", "").split(","):
                if m := re.search(r"(\d)\|(\d+)(:\d+)?(am|pm)-(\d+)(:\d+)?(am|pm)", rule):
                    day, start_hour, start_minute, start_zone, end_hour, end_minute, end_zone = m.groups()
                    start_time = f'{start_hour}{start_minute or ":00"}{start_zone}'
                    end_time = f'{end_hour}{end_minute or ":00"}{end_zone}'
                    oh.add_range(DAYS[int(day) - 1], start_time, end_time, time_format="%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()

            yield item
