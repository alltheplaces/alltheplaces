import re
from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.react_server_components import parse_rsc


class DuckDonutsSpider(Spider):
    name = "duck_donuts"
    allowed_domains = ["www.duckdonuts.com"]
    start_urls = [
        "https://www.duckdonuts.com/directory",
        "https://www.duckdonuts.com/locations/international-locations",
    ]
    item_attributes = {"brand": "Duck Donuts", "brand_wikidata": "Q54958282"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if "international" in response.url:
            yield from self.parse_international(response)
            return

        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        data = dict(parse_rsc("".join([s for n, s in objs]).encode()))

        def resolve_reference(obj):
            if isinstance(obj, str) and obj.startswith("$"):
                try:
                    return data[int(obj.removeprefix("$"), 16)]
                except (KeyError, ValueError):
                    return obj
            return obj

        def find_locations(obj):
            obj = resolve_reference(obj)
            if isinstance(obj, dict):
                if "extref" in obj and "address" in obj:
                    yield obj
                else:
                    for value in obj.values():
                        yield from find_locations(value)
            elif isinstance(obj, list):
                for value in obj:
                    yield from find_locations(value)

        for location in find_locations(data):
            item = DictParser.parse({**location, **location["address"]})
            item["ref"] = location["extref"]
            item["branch"] = item.pop("name").removeprefix("Duck Donuts").strip(" -")
            item["street_address"] = item.pop("street")

            business_hours = location["hours"].get("business") if isinstance(location["hours"], dict) else None
            if isinstance(business_hours, dict):
                opening_hours = OpeningHours()
                for day, day_hours in business_hours.items():
                    if not day_hours["start"]:
                        opening_hours.set_closed(sanitise_day(day))
                        continue
                    opening_hours.add_range(
                        sanitise_day(day), day_hours["start"][11:16], day_hours["end"][11:16], "%H:%M"
                    )
                item["opening_hours"] = opening_hours

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "donut"
            yield item

    def parse_international(self, response: Response) -> Iterable[Feature]:
        for card in response.css("div[class*='LocationCards_card__']"):
            heading = card.css("[class*='card_vendor']::text").get()
            lines = card.css("[class*='card_location'] div::text").getall()
            city = lines[1].split(",")[0]
            postcode = None
            if match := re.match(r"^(.*?)\s+(\d{4,7}|[A-Z]{1,2}\d[A-Z\d]?\s\d[A-Z]{2})$", city):
                city, postcode = match.groups()
            item = DictParser.parse(
                {
                    "name": heading,
                    "street_address": lines[0],
                    "city": city,
                    "postcode": postcode,
                    "country": heading.partition(" - ")[0],
                    "phone": card.css("a[href^='tel:']::attr(href)").get(),
                }
            )
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
            item["branch"] = item.pop("name").partition(" - ")[2]
            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "donut"
            yield item
