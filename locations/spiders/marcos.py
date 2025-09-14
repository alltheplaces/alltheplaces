import json
import time

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


def minutes_to_time(minutes: int):
    return time.gmtime(minutes * 60)


class MarcosSpider(Spider):
    name = "marcos"
    item_attributes = {
        "brand": "Marco's Pizza",
        "brand_wikidata": "Q6757382",
    }
    start_urls = ["https://www.marcos.com/api/v1.0/locations/stores/A5985C38-D485-4240-8C01-931F7186D567"]

    def parse(self, response, **kwargs):
        for location in json.loads(response.json()["result"]):
            item = DictParser.parse(location)
            item["ref"] = location["SCODE"] or location["SID"]
            item["street_address"] = merge_address_lines(
                [location["ADD1"], location["ADD2"], location["ADD3"], location["ADD4"], location["ADD5"]]
            )
            item["state"] = location["STA"]
            oh = OpeningHours()
            for day in location["HRs"]:
                oh.add_range(
                    DAYS_FROM_SUNDAY[day["WID"]],
                    minutes_to_time(day["SMIN"]),
                    minutes_to_time(day["EMIN"]),
                )
            item["opening_hours"] = oh

            yield item
