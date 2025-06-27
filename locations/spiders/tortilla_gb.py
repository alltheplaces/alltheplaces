import json
import re

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class TortillaGBSpider(JSONBlobSpider):
    name = "tortilla_gb"
    item_attributes = {"brand": "Tortilla", "brand_wikidata": "Q21006828"}
    start_urls = ["https://www.tortilla.co.uk/restaurants"]

    def parse(self, response):
        match = re.search(r'\\"restaurants\\"\:([^\n]+)\}\],false\]\}\],\[\\"\$\\",', response.text)
        data = match.group(1).replace('\\"', '"')

        json_data = json.loads(data)
        for location in json_data:
            item = DictParser.parse(location["content"])
            item["branch"] = item.pop("name")
            item["ref"] = item["branch"].replace(" ","")
            if item["phone"]:
                item["phone"].replace(" ", "")
            item["website"] = "https://www.tortilla.co.uk/" + location["full_slug"]

            apply_category(Categories.FAST_FOOD, item)

            yield item
