import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours, sanitise_day


class SupercontiITSpider(Spider):
    name = "superconti_it"
    item_attributes = {"brand": "Superconti", "brand_wikidata": "Q69381940"}
    start_urls = ["https://www.superconti.eu/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = ", ".join(filter(None, [location.pop("address"), location.pop("address2")]))

            item = DictParser.parse(location)

            item["name"] = location["store"]
            item["country"] = "IT"

            item["opening_hours"] = OpeningHours()
            for day, start_time, end_time in re.findall(
                r"<td>(\w+)</td><td><time>(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", location["hours"]
            ):
                if f := sanitise_day(day, DAYS_IT):
                    item["opening_hours"].add_range(f, start_time, end_time)

            yield item
