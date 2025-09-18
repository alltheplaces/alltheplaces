from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class BudniDESpider(Spider):
    name = "budni_de"
    allowed_domains = ["www.budni.de"]
    start_urls = ["https://www.budni.de/filialen"]
    item_attributes = {"brand": "Budni", "brand_wikidata": "Q1001516"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        def resolve_reference(obj):
            if isinstance(obj, str) and obj.startswith("$"):
                reference = int(store.removeprefix("$"), 16)
                return data[reference]
            else:
                return obj

        for store in resolve_reference(DictParser.get_nested_key(data, "markets")):
            store = resolve_reference(store)
            for key, value in store.items():
                store[key] = resolve_reference(value)
            # Rename keys to help DictParser find the content
            store["address"] = store.pop("contact")
            store["address"]["street_address"] = store["address"].pop("streetAndNumber")
            store["location"] = store["address"]

            item = DictParser.parse(store)
            item["website"] = "https://www.budni.de/filialen/{}".format(item["ref"])
            if item["name"].startswith("budni - "):
                item["branch"] = item.pop("name").removeprefix("budni - ")
            hours = OpeningHours()
            hours.add_ranges_from_string(store["workingDaysSummary"], DAYS_DE)
            item["opening_hours"] = hours
            yield item
