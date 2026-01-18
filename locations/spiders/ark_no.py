from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class ArkNOSpider(Spider):
    name = "ark_no"
    allowed_domains = ["www.ark.no"]
    start_urls = ["https://www.ark.no/butikker"]
    item_attributes = {"brand": "Ark", "brand_wikidata": "Q11958706"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        def resolve_reference(obj):
            if isinstance(obj, str) and obj.startswith("$"):
                reference = int(obj.removeprefix("$"), 16)
                return data[reference]
            else:
                return obj

        for store in resolve_reference(DictParser.get_nested_key(data, "stores")):
            store = resolve_reference(store)
            if isinstance(store, dict):
                for key, value in store.items():
                    store[key] = resolve_reference(value)

                item = DictParser.parse(store)

                item["branch"] = item.pop("name").removeprefix("ARK").strip()

                opening_hours = OpeningHours()
                for key, day in (
                    ("mondayOpeningHours", "Mo"),
                    ("tuesdayOpeningHours", "Tu"),
                    ("wednesdayOpeningHours", "We"),
                    ("thursdayOpeningHours", "Th"),
                    ("fridayOpeningHours", "Fr"),
                    ("saturdayOpeningHours", "Sa"),
                    ("sundayOpeningHours", "Su"),
                ):
                    if not (day_hours := store.get(key)):
                        continue
                    if not day_hours.get("isOpen"):
                        opening_hours.set_closed(day)
                        continue
                    opening_hours.add_range(day, day_hours.get("openFrom"), day_hours.get("openTo"), "%H:%M:%S")
                
                item["opening_hours"] = opening_hours

                yield item
