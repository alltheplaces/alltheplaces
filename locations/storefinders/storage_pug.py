import re
from typing import Any, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|([A-Za-z_$][\w$]*)(?!\s*[:\w$])')


class StoragePugSpider(Spider):
    """
    Storage Pug (https://storagepug.com/) builds Nuxt.js websites for self
    storage operators. The `/view-locations` page of these websites links to a
    `state.js` payload which contains every location, including coordinates,
    phone number and office hours. The payload is minified, with repeated
    literals hoisted into the arguments of an enclosing function, so these are
    substituted back in before the locations are read.

    To use this storefinder, specify `start_urls` as a list with the
    `/view-locations` URL of the website. If clean ups or additional field
    extraction is required, override parse_item.
    """

    dataset_attributes: dict = {"source": "api", "api": "storagepug.com"}

    def parse(self, response: TextResponse) -> Iterable[Request]:
        state_path = re.search(r"/_nuxt/static/[^\"']+/state\.js", response.text).group(0)
        yield Request(response.urljoin(state_path), callback=self.parse_state)

    def parse_state(self, response: TextResponse) -> Iterable[Feature]:
        nuxt_data = response.text
        parameter_names = re.search(r"function\(([\w$,]+)\)", nuxt_data).group(1).split(",")
        arguments_start = nuxt_data.rfind("}}}}(") + 5
        parameter_values = chompjs.parse_js_object("[" + nuxt_data[arguments_start : nuxt_data.rfind("))")] + "]")
        parameters = dict(zip(parameter_names, parameter_values))
        literals = {"!0": True, "!1": False, "void 0": None, "null": None, "true": True, "false": False}

        def resolve(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: resolve(sub) for key, sub in value.items()}
            if isinstance(value, list):
                return [resolve(sub) for sub in value]
            if isinstance(value, str) and value.startswith("\0"):
                value = parameters[value[1:]]
            if isinstance(value, str):
                return literals.get(value, value)
            return value

        locations_start = nuxt_data.index("locations:[{id:") + len("locations:")
        # Identifiers are marked so that they can't be confused with string literals of the same text.
        marked = _TOKEN.sub(
            lambda match: (
                match.group(0)
                if match.group(1) is None or match.group(1) in ("null", "true", "false")
                else f'"\\u0000{match.group(1)}"'
            ),
            nuxt_data[locations_start:arguments_start],
        )
        for location in resolve(chompjs.parse_js_object(marked)):
            if location.get("status") != "Live":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["id"]
            item["branch"] = item.pop("name", None)
            item["website"] = response.urljoin(f"/locations/{location['url_slug']}")
            item["street_address"] = ", ".join(
                filter(None, [location["address"]["street_1"], location["address"]["street_2"]])
            )
            item["state"] = location["address"]["state_province"]
            item["postcode"] = location["address"]["postal"]
            item["lat"] = location["address"]["lat"]
            item["lon"] = location["address"]["lon"]

            for hours in location["hours"]:
                if hours["type"] != "office":
                    continue
                item["opening_hours"] = OpeningHours()
                for rule in hours["items"]:
                    for day in rule["days"].split(","):
                        if rule["is_closed"]:
                            item["opening_hours"].set_closed(day)
                        elif rule["is_open_24_hours"]:
                            item["opening_hours"].add_range(day, "00:00", "24:00")
                        else:
                            item["opening_hours"].add_range(day, rule["open"], rule["close"])

            apply_category(Categories.SHOP_STORAGE_RENTAL, item)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
