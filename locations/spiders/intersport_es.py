import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours


class IntersportESSpider(scrapy.Spider):
    start_urls = ["https://www.intersport.es/tiendas"]

    name = "intersport_es"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}

    def parse(self, response, **kwargs):
        store_json = response.xpath('//script/text()[contains(., "stores")]').re_first(r"var stores\s*=\s*(.*);")
        stores = json.loads(store_json)
        for store in stores:
            store["ref"] = store.pop("id_store")
            store["name"] = store["name"].title()
            store["website"] = "https://www.intersport.es/tiendas?idStore=" + str(store["ref"])
            item = DictParser.parse(store)
            if "business_hours" in store and store["business_hours"] is not None:
                item["opening_hours"] = self.parse_opening_hours(store["business_hours"])
            yield item

    def parse_opening_hours(self, hours_definition):
        closed = {"", "Cerrado", "Cerrada"}
        re_list = re.compile(r" y |, ")
        re_interval = re.compile(r" a |-")
        hours = OpeningHours()
        for day_definition in hours_definition:
            day_en = DAYS_ES[day_definition["day"].strip()]
            for intervals in day_definition["hours"]:
                for interval in re_list.split(intervals):
                    if interval not in closed:
                        open_time, close_time = re_interval.split(interval)
                        hours.add_range(day_en, open_time.strip(), close_time.strip())
        return hours
