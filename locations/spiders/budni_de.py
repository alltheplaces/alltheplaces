from typing import Any, Iterable

import scrapy
from chompjs import chompjs
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class BudniDESpider(scrapy.Spider):
    name = "budni_de"
    allowed_domains = ["www.budni.de"]
    start_urls = ["https://www.budni.de/filialen"]
    item_attributes = {"brand": "Budni", "brand_wikidata": "Q1001516"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))
        # Look for a list consisting only of '$123' references. This is the list of stores.
        store_list = []
        for key, value in data.items():
            if isinstance(value, list):
                if all(isinstance(i, str) and i.startswith("$") for i in value):
                    store_list = value
        for store_reference in store_list:
            # Sub-objects are '$123' references and need to be fetched from 'data'
            reference = int(store_reference.removeprefix("$"), 16)
            store = data[reference]
            for key, value in store.items():
                if isinstance(value, str) and value.startswith("$"):
                    value_ref = int(value.removeprefix("$"), 16)
                    store[key] = data[value_ref]
            # Rename keys to help DictParser find the content
            store["address"] = store.pop("contact")
            store["address"]["street_address"] = store["address"].pop("streetAndNumber")
            store["location"] = store["address"]

            item = DictParser.parse(store)
            item["website"] = "https://www.budni.de/filialen/{}".format(item["ref"])
            if item["name"].startswith("budni - "):
                item["branch"] = item["name"].removeprefix("budni - ")
                item["name"] = "Budni"
            hours = OpeningHours()
            hours.add_ranges_from_string(store["workingDaysSummary"], DAYS_DE)
            item["opening_hours"] = hours
            yield item
