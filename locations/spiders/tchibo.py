import re

from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider

"""
Covers Following Countries : AT,DE,CZ,SK,HU,PL,CH,TR
"""


class TchiboSpider(StructuredDataSpider):
    name = "tchibo"
    item_attributes = {"brand": "Tchibo", "brand_wikidata": "Q564213"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.tchibo.de/service/storefinder/api/plugins/storefinder/storefinder/api/stores?viewLat=0&viewLng=0&precision=1000000&size=100&page=0&storeTypeFilters=Filiale",
    ]

    def parse(self, response, **kwargs):
        for store in response.json().get("content"):
            [store.update(store.pop(key)) for key in ["locationGeographicDto", "addressDto"]]
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            oh = OpeningHours()

            for rule, time in store.get("daysDto").items():
                day = sanitise_day(rule)
                for k in time.keys():
                    if time[k] == "null":
                        continue
                    if k in ["morningOpening", "afternoonOpening"]:
                        open_time = time.get(k)
                    elif k in ["morningClosing", "afternoonClosing"]:
                        close_time = time.get(k)
                        if open_time and close_time in ["null", ""]:
                            continue

                        oh.add_range(day, open_time, close_time.replace("23:59:59", "23:59"))
            item["opening_hours"] = oh

            yield item

        current_page = response.json()["number"]
        pages = response.json()["totalPages"]
        if current_page < pages:
            url = re.sub(r"page=\d+", f"page={current_page + 1}", response.url)
            yield JsonRequest(url=url)
