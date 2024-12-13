import re

from scrapy import Selector

from locations.hours import OpeningHours, sanitise_day
from locations.storefinders.woosmap import WoosmapSpider


class TheWorksSpider(WoosmapSpider):
    name = "the_works"
    item_attributes = {"brand": "The Works", "brand_wikidata": "Q7775853"}
    key = "woos-c51a7170-fe29-3221-a27e-f73187126d1b"
    origin = "https://www.theworks.co.uk"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = f'https://www.theworks.co.uk/Store?storeId={item["ref"]}'
        if timing := feature.get("properties", {}).get("user_properties", {}).get("storeHours"):
            store_hours = Selector(text=timing).xpath('//*[@class="store-hours-usual"]')
            if all("closed" in hours.lower() for hours in store_hours.xpath('.//*[@class="hours"]/text()').getall()):
                return  # permanently closed
            item["opening_hours"] = OpeningHours()
            for rule in store_hours.xpath(".//p"):
                if day := sanitise_day(rule.xpath('.//*[@class="day"]/text()').get(default="").strip(":")):
                    hours = rule.xpath('.//*[@class="hours"]/text()').get(default="")
                    for open_time, close_time in re.findall(r"(\d+:\d+)[-\s]+(\d+:\d+)", hours):
                        item["opening_hours"].add_range(day, open_time, close_time)
        yield item
