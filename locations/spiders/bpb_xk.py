import json
import re

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class BpbXkSpider(JSONBlobSpider):
    name = "bpb_xk"
    item_attributes = {
        "brand": "Banka Për Biznes",
        "brand_wikidata": "Q16349919",
    }
    start_urls = ["https://www.bpbbank.com/front/dist/js/main.js"]

    def extract_json(self, response):
        return json.loads(re.search(r"var locations = jQuery.parseJSON\(\'(.*)\'\);", response.text).group(1))

    def post_process_item(self, item, response, location):
        item.pop("name")  # title is address, not name
        item.pop("city")  # is not accurate
        item["ref"] = f"{location.get('title','').replace(' ', '-')}-{location['type']}"
        item["addr_full"] = location["title"]
        item["phone"] = Selector(text=location["text"]).xpath("//p/text()").re_first(r"Tel: (.*)")
        if location["type"] == 1:
            apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.ATM, item)
        # TODO: hours
        yield item
