from typing import Any

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class SmiggleSpider(JSONBlobSpider):
    name = "smiggle"
    item_attributes = {"brand": "Smiggle", "brand_wikidata": "Q7544536"}
    start_urls = ["https://www.smiggle.co.uk/shop/en/smiggleuk/stores"]
    drop_attributes = {"facebook", "twitter"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def extract_json(self, response: Response) -> Any:
        js_blob = "[" + response.text.split("const storeData = [", 1)[1].split("]", 1)[0] + "]"
        return parse_js_object(js_blob)

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Any:
        item["branch"] = item.pop("name")
        item["ref"] = location["locId"]
        item["website"] = location["storeURL"]
        apply_category(Categories.SHOP_STATIONERY, item)
        if item["phone"]:
            item["phone"] = item["phone"].strip()
        if item["postcode"]:
            postcode = item["postcode"].strip()
            item["postcode"] = postcode if postcode != "." else None
        item["street_address"] = clean_address([location["shopAddress"], location["streetAddress"]])
        yield item
