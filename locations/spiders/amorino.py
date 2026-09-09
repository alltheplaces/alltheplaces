import re

import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class AmorinoSpider(JSONBlobSpider):
    name = "amorino"
    item_attributes = {
        "brand": "Amorino",
        "brand_wikidata": "Q2843884",
    }
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

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature.pop("place_id", "")

    def post_process_item(self, item, response, location):
        apply_category(Categories.ICE_CREAM, item)

        item["branch"] = item.pop("name")
        item["addr_full"] = location.pop("adress")

        slug = location.get("slug")
        if slug:
            item["website"] = "https://www.amorino.com/stores/" + slug

        if item.get("phone") is None:
            item["phone"] = location.get("google_phone").removeprefix("'")

        if (item.get("country") or "") in ["FR", "France", "France "]:
            match = re.search(r"\b\d{5}\b", item.get("addr_full"))
            item["postcode"] = match.group() if match else None

        yield item
