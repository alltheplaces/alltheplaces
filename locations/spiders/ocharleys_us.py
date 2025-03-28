import json
import re

import chompjs

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class OcharleysUSSpider(JSONBlobSpider):
    name = "ocharleys_us"
    item_attributes = {"brand": "O'Charley's", "brand_wikidata": "Q7071703"}
    start_urls = ["https://www.ocharleys.com/locations/"]

    def extract_json(self, response):
        script = response.xpath("//script[starts-with(text(), 'window.__NUXT__=')]/text()").get()
        param_names = script[script.find("function(") + len("function(") : script.find(")")].split(",")
        param_values = json.loads("[" + script[script.rfind("(") + 1 : script.rfind("))")] + "]")
        body = script[script.find("{") : script.rfind("}") + 1]
        for name, value in zip(param_names, param_values):
            body = re.sub(":" + re.escape(name) + r"\b", ":" + json.dumps(value).replace("\\", "\\\\"), body)
        return chompjs.parse_js_object(body[body.find("allLocations") :])

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(feature["path"])
        item["street_address"] = item.pop("addr_full")

        oh = OpeningHours()
        for line in feature["hours"]:
            oh.add_range(line["day"], line["open"], line["close"])
        item["opening_hours"] = oh

        yield item
