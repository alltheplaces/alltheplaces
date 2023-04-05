import re

import scrapy

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature


class CurvesNLSpider(scrapy.Spider):
    name = "curves_nl"
    item_attributes = {"brand": "Curves International", "brand_wikidata": "Q5196080"}
    start_urls = [
        "https://curves.nl/wp-admin/admin-ajax.php?action=store_search&max_results=25000&search_radius=10000000&autoload=1"
    ]

    def parse(self, response):
        stores = response.json()
        for store in stores:
            item = Feature()
            common_keys = ["lat", "phone", "city", "email", "state"]
            for key in common_keys:
                item[key] = store[key]
            item["ref"] = store["id"]
            item["name"] = store["store"]
            item["lon"] = store["lng"]
            item["street_address"] = " ".join([store["address"], store["address2"]])
            item["website"] = "https://curves.nl" + store["url"]
            item["opening_hours"] = self.parse_opening_hours(store["hours"])

            yield item

    def parse_opening_hours(self, opening_hours):
        oh = OpeningHours()
        regex = "(<td>)(.*?)(</td>)"
        regex_hours = "(<time>)(.*?)(</time>)"
        parsed_opening_hours = re.findall(pattern=regex, string=opening_hours)
        for i in range(0, len(parsed_opening_hours), 2):
            day = parsed_opening_hours[i][1]
            hours_list = re.findall(regex_hours, parsed_opening_hours[i + 1][1])
            for hours in hours_list:
                oh.add_ranges_from_string(ranges_string=day + " " + hours[1], days=DAYS_NL, delimiters=[" - "])
        return oh.as_opening_hours()
