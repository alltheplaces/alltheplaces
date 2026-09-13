from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AmorinoSpider(JSONBlobSpider):
    name = "amorino"
    item_attributes = {"brand": "Amorino", "brand_wikidata": "Q2843884"}
    start_urls = ["https://www.amorino.com/storelocator"]

    def extract_json(self, response):
        script = response.xpath('//script[contains(text(), "storelocator:")]/text()').get()

        start_script, rest = script.split("return {", 1)
        splitted_script = rest.split("}(")
        object_string = "{" + splitted_script[0] + "}"
        end_script = "[" + splitted_script[1].replace(")", "]")

        param_values = chompjs.parse_js_object(end_script)
        param_keys = chompjs.parse_js_object("[" + start_script.split("function(")[1].replace(")", "]"))
        replacements = dict(zip(param_keys, param_values))

        data = chompjs.parse_js_object(object_string)["state"]["storelocator"]["shops"]

        def replace_values(obj):
            if isinstance(obj, str):
                if obj in param_keys:
                    return replacements[obj]
                else:
                    return obj
            elif isinstance(obj, dict):
                for k in obj.keys():
                    obj[k] = replace_values(obj[k])
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    obj[i] = replace_values(obj[i])
            return obj

        return replace_values(data)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = feature.get("adress")
        item["extras"]["ref:google:place_id"] = feature.get("place_id")

        if slug := feature.get("slug"):
            item["website"] = "https://www.amorino.com/stores/{}".format(slug)

        if not item.get("phone"):
            if google_phone := feature.get("google_phone"):
                item["phone"] = google_phone.removeprefix("'")

        apply_category(Categories.ICE_CREAM, item)
        yield item
