import json

import scrapy
from requests import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class WelkoopNLSpider(scrapy.Spider):
    name = "welkoop_nl"
    item_attributes = {"brand": "Welkoop", "brand_wikidata": "Q72799253"}
    start_urls = ["https://www.welkoop.nl/winkels"]

    def parse(self, response: Response, **kwargs):
        data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["__PRELOADED_STATE__"][
            "__reactQuery"
        ]["queries"]
        for location_data in data:
            if data := location_data.get("state").get("data").get("data"):
                for location in data:
                    item = DictParser.parse(location)
                    item["street_address"] = merge_address_lines([location.get("address2"), location.get("address1")])
                    item["branch"] = item.pop("name").replace("Welkoop ", "")
                    oh = OpeningHours()
                    for hours_data in json.loads(location.get("store_hours")):
                        day = sanitise_day(list(hours_data.get("day").values())[0], DAYS_NL)
                        open_close_time_data = hours_data.get("hours")
                        if open_close_time_data == "Gesloten":
                            oh.set_closed(day)
                        else:
                            for open_close_time in open_close_time_data:
                                print(open_close_time)
                                open_time = open_close_time.get("open")
                                close_time = open_close_time.get("close")
                                oh.add_range(day=day, open_time=open_time, close_time=close_time)
                    item["opening_hours"] = oh

                    yield item
