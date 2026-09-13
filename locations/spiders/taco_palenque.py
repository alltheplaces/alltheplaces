import re
from typing import Any, Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


def resolve_parameters(obj: Any, parameters: dict[str, Any]) -> Any:
    """Substitute the literals hoisted into the arguments of a minified Nuxt payload."""
    if isinstance(obj, str):
        return parameters.get(obj, obj)
    elif isinstance(obj, list):
        return [resolve_parameters(sub, parameters) for sub in obj]
    elif isinstance(obj, dict):
        return {key: resolve_parameters(value, parameters) for key, value in obj.items()}
    else:
        return obj


class TacoPalenqueSpider(JSONBlobSpider):
    name = "taco_palenque"
    item_attributes = {"brand": "Taco Palenque", "brand_wikidata": "Q7673965"}
    start_urls = ["https://tacopalenque.com/locations/"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        nuxt_data = response.xpath("//script[starts-with(text(), 'window.__NUXT__')]/text()").get()

        parameter_names = re.search(r"function\(([\w_$,]+)\)", nuxt_data).group(1).split(",")
        begin_parameter_values = nuxt_data.rfind("}}}}(") + 5
        parameter_values = chompjs.parse_js_object("[" + nuxt_data[begin_parameter_values : nuxt_data.rfind(")")] + "]")

        # Locations are grouped by state and then by city, so gather each of the per-city arrays.
        locations = []
        for city in re.finditer(r"locations:\[", nuxt_data[:begin_parameter_values]):
            locations.extend(
                resolve_parameters(
                    chompjs.parse_js_object(nuxt_data[city.end() - 1 :]), dict(zip(parameter_names, parameter_values))
                )
            )
        return locations

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["website"] = response.urljoin(feature["path"] + "/")

        item["opening_hours"] = OpeningHours()
        for daily_hours in feature["hours"]:
            if daily_hours.get("is24") == "!0":
                item["opening_hours"].add_range(daily_hours["day"], "00:00", "24:00")
            elif daily_hours["open"]:
                item["opening_hours"].add_range(daily_hours["day"], daily_hours["open"], daily_hours["close"])

        apply_category(Categories.FAST_FOOD, item)

        yield item
