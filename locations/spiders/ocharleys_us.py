import json
import re

import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OcharleysUSSpider(Spider):
    name = "ocharleys_us"
    item_attributes = {"brand": "O'Charley's", "brand_wikidata": "Q7071703"}
    start_urls = ["https://www.ocharleys.com/locations/"]

    def parse(self, response):
        nuxt_data = response.xpath("//script[starts-with(text(), 'window.__NUXT__')]/text()").get()

        parameter_names = re.search(r"function\(([\w_$,]+)\)", nuxt_data).group(1).split(",")
        begin_parameter_values = nuxt_data.rfind("}}}}(") + 5
        end_parameter_values = nuxt_data.rfind("));")
        parameter_values = json.loads("[" + nuxt_data[begin_parameter_values:end_parameter_values] + "]")
        parameters = dict(zip(parameter_names, parameter_values))

        def resolve(obj):
            if isinstance(obj, str) and obj in parameters:
                return parameters[obj]
            elif isinstance(obj, list):
                return [resolve(sub) for sub in obj]
            elif isinstance(obj, dict):
                return {k: resolve(v) for k, v in obj.items()}
            else:
                return obj

        return_value = chompjs.parse_js_object(nuxt_data[nuxt_data.find("return") + 6 : begin_parameter_values])

        for location in map(resolve, DictParser.get_nested_key(return_value, "allLocations")):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(location["path"])

            oh = OpeningHours()
            for daily_hours in location["hours"]:
                oh.add_range(daily_hours["day"], daily_hours["open"], daily_hours["close"])
            item["opening_hours"] = oh

            yield item
